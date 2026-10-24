"""きゅー太しんだん：コアロジック（診断・キャラ合成・シール画像生成）
画面(main.py)から独立しているので、単体テストや素材チェックにも使えます。"""
import hashlib, random, sys, glob
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops

BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))   # exe化後も動く
PARTS = BASE / "assets" / "parts"
OUTPUT = Path(__file__).parent / "output"

SIZE = 1024                      # 全パーツ共通のキャンバスサイズ
DPI, STICKER_MM = 300, 60        # シールは60mm角 / 300dpi
PX = int(STICKER_MM / 25.4 * DPI)
NAME_MAX = 6
RARE_CHANCE = 0.03

COLORS = {
    "あか": (255, 125, 125), "オレンジ": (255, 175, 95),
    "きいろ": (255, 228, 105), "みどり": (135, 215, 145),
    "みずいろ": (135, 225, 238), "あお": (125, 175, 255),
    "むらさき": (195, 155, 240), "ピンク": (255, 165, 208),
}

# ---- 診断テキスト（パーツ名 → 表示名。パーツを足したらここにも1行足す） ----
FACE_ADJ = {"face01": "げんきな", "face02": "ねぼすけな", "face03": "のんびりやの",
            "face04": "いたずらずきな", "face05": "はずかしがりやの"}
HAT_NAME = {"hat01": "パーティーぼうの", "hat02": "おでかけぼうの", "hat03": "おうかんの",
            "hat04": "コックさんの", "hat05": "リボンの", None: ""}
ITEM_NAME = {"item01": "ふうせん", "item02": "おほしさま", "item03": "おはな",
             "item04": "ハート", "item05": "アイス", None: "なし"}
MESSAGES = [
    "きょうは ともだちに こえを かけると いいことあるよ！",
    "ちょっと むずかしいことに チャレンジすると のびるよ！",
    "おうちの人に ありがとうを いうと ラッキー！",
    "あたらしい ことを ひとつ ためしてみよう！",
    "えがおで あいさつすると みんなが ハッピーになるよ！",
    "すきな ことを とことん たのしむと ひらめくよ！",
    "だれかに やさしくすると きみにも いいことが くるよ！",
    "きょうは ぐうぜん ステキな であいが あるかも！",
    "ゆっくり やすむと あしたは もっと げんきだよ！",
    "おもいきって やってみると うまくいくよ！",
    "ともだちと わけっこすると しあわせが ふえるよ！",
    "ふしぎだな？と おもったら しらべてみよう！",
]


def find_font():
    cands = sorted(glob.glob(str(BASE / "assets" / "fonts" / "*.[to]t[fc]")))
    cands += sorted(glob.glob(str(BASE / "*.[to]t[fc]")))   # 一番上の階層に置かれた場合も探す
    cands += [  # 同梱フォントが無い場合のシステムフォント
        "C:/Windows/Fonts/meiryob.ttc", "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/YuGothB.ttc", "C:/Windows/Fonts/msgothic.ttc",
        "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    ]
    for p in cands:
        if Path(p).exists():
            return p
    raise FileNotFoundError("日本語フォントが見つかりません。assets/fonts/ にTTF/OTFを入れてください")


def make_seed(month, day, color):
    # hash()は起動ごとに値が変わるのでhashlibを使う
    return int(hashlib.sha256(f"{month}-{day}-{color}".encode()).hexdigest(), 16)


def _pick(rng, category, none_chance=0.0):
    r = rng.random()                       # 乱数の消費数を一定に保つ
    files = sorted((PARTS / category).glob("*.png"))
    if not files or r < none_chance:
        return None
    return rng.choice(files)


def _gold_background():
    g = Image.radial_gradient("L").resize((SIZE, SIZE))
    g = ImageChops.invert(g)
    gold = Image.merge("RGB", [g.point(lambda v: 255), g.point(lambda v: 190 + v // 5),
                               g.point(lambda v: 40 + v // 2)])
    rays = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(rays)
    import math
    for i in range(16):
        a0, a1 = i * math.tau / 16, (i + 0.5) * math.tau / 16
        pts = [(SIZE / 2, SIZE / 2)] + [(SIZE / 2 + 700 * math.cos(a), SIZE / 2 + 700 * math.sin(a)) for a in (a0, a1)]
        d.polygon(pts, fill=(255, 255, 255, 90))
    mask = Image.new("L", (SIZE * 2, SIZE * 2), 0)
    ImageDraw.Draw(mask).ellipse((80, 80, SIZE * 2 - 80, SIZE * 2 - 80), fill=255)
    mask = mask.resize((SIZE, SIZE), Image.LANCZOS)
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.paste(Image.alpha_composite(gold.convert("RGBA"), rays), (0, 0), mask)
    return out


def compose_character(month, day, color):
    """入力 → (キャラ画像, 選ばれたパーツ, rng, レアか)。同じ入力なら必ず同じ結果。"""
    rng = random.Random(make_seed(month, day, color))
    ch = {"background": _pick(rng, "background"), "face": _pick(rng, "face"),
          "outfit": _pick(rng, "outfit", 0.15), "hat": _pick(rng, "hat", 0.3),
          "item": _pick(rng, "item", 0.3)}
    rare = rng.random() < RARE_CHANCE

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    if rare:
        canvas = Image.alpha_composite(canvas, _gold_background())
    elif ch["background"]:
        canvas = Image.alpha_composite(canvas, Image.open(ch["background"]).convert("RGBA"))

    body = Image.open(PARTS / "body" / "base.png").convert("RGBA")
    tint = Image.new("RGBA", body.size, COLORS[color] + (255,))
    canvas = Image.alpha_composite(canvas, ImageChops.multiply(body, tint))  # 白い所だけ色が付く
    for cat in ("face", "outfit", "hat", "item"):
        if ch[cat]:
            canvas = Image.alpha_composite(canvas, Image.open(ch[cat]).convert("RGBA"))
    return canvas, ch, rng, rare


def make_fortune(ch, rng, color, rare):
    stem = lambda k: ch[k].stem if ch[k] else None
    title = f"{HAT_NAME.get(stem('hat'), '')}{FACE_ADJ.get(stem('face'), 'ふしぎな')}きゅー太"
    if rare:
        title = "スーパーレア！" + title
    return {"title": title, "message": rng.choice(MESSAGES), "lucky_color": color,
            "lucky_item": ITEM_NAME.get(stem("item"), "ひみつ"), "rare": rare}


def _fit_font(draw, text, font_path, max_px, max_w):
    size = max_px
    while size > 12:
        f = ImageFont.truetype(font_path, size)
        b = draw.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= max_w:
            return f, b
        size -= 4
    return f, b


def next_number():
    OUTPUT.mkdir(exist_ok=True)
    return len(list(OUTPUT.glob("*.png"))) + 1


def make_sticker(char_img, name, title, number, save=True):
    """印刷用（60mm角・300dpi）のシール画像を作る。"""
    fp = find_font()
    s = PX
    sticker = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    big = Image.new("L", (s * 2, s * 2), 0)
    ImageDraw.Draw(big).rounded_rectangle((0, 0, s * 2 - 1, s * 2 - 1), radius=150, fill=255)
    sticker.paste((255, 255, 255, 255), (0, 0), big.resize((s, s), Image.LANCZOS))

    d = ImageDraw.Draw(sticker)
    d.rounded_rectangle((4, 4, s - 5, s - 5), radius=75, outline=(225, 225, 225, 255), width=3)

    ill = char_img.copy()
    ill.thumbnail((int(s * 0.68), int(s * 0.68)), Image.LANCZOS)
    sticker.alpha_composite(ill, ((s - ill.width) // 2, int(s * 0.03)))

    f, b = _fit_font(d, name, fp, int(s * 0.16), int(s * 0.86))
    d.text(((s - (b[2] - b[0])) // 2 - b[0], int(s * 0.715)), name, font=f, fill=(70, 70, 70, 255))
    f2, b2 = _fit_font(d, title, fp, int(s * 0.065), int(s * 0.88))
    d.text(((s - (b2[2] - b2[0])) // 2 - b2[0], int(s * 0.90)), title, font=f2, fill=(130, 130, 130, 255))

    path = None
    if save:
        OUTPUT.mkdir(exist_ok=True)
        path = OUTPUT / f"{number:03d}_{datetime.now():%H%M%S}.png"
        sticker.save(path, dpi=(DPI, DPI))
    return sticker, path
