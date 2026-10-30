"""きゅー太しんだん：コアロジック（診断・キャラ合成・シール画像生成）
画面(main.py)から独立しているので、単体テストや素材チェックにも使えます。"""
import hashlib, random, sys, glob
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops

FROZEN = getattr(sys, "frozen", False)                         # exe化されているか
BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))   # 素材（assets）の場所
APP_DIR = Path(sys.executable).parent if FROZEN else Path(__file__).parent
PARTS = BASE / "assets" / "parts"
CHARS = BASE / "assets" / "chars"        # 完成した1枚絵のポーズ（r1〜r4：星の段階ごとのフォルダ）
OUTPUT = APP_DIR / "output"                                    # exeの隣に保存（一時フォルダに入れない）

SIZE = 1024                      # 全パーツ共通のキャンバスサイズ
DPI, STICKER_MM = 300, 60        # シールは60mm角 / 300dpi
PX = int(STICKER_MM / 25.4 * DPI)
NAME_MAX = 6
# レア度（★の数）。しきい値は「乱数がこの値より小さければその段階」。
#   ★★★★ 1% / ★★★ 9% / ★★ 30% / ★ 60%
RARITY_STEPS = [(0.01, 4), (0.10, 3), (0.40, 2)]    # それ以外は★1
FORCE_RARITY = None     # 動作確認用：1〜4 を入れるとその段階に固定（確認後は必ず None に戻す）
RARITY_NOTE = {         # どの段階も「良さ」を伝える言葉にする（がっかり防止）
    1: "いちばん なかよしの きゅー太！",
    2: "ちょっと めずらしい きゅー太！",
    3: "キラキラの めずらしい きゅー太！",
    4: "スーパーレア！ すごい きゅー太！",
}
RARITY_COLOR = {1: (170, 170, 170), 2: (90, 170, 255), 3: (255, 190, 40), 4: (255, 130, 0)}   # 星・縁の色
RARITY_BORDER = {1: 3, 2: 10, 3: 16, 4: 22}                                                   # シールの縁の太さ

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
# ポーズごとの診断名・ラッキーアイテム（ポーズを足したらここに1行足す。無ければ自動で決まる）
POSE_ADJ = {"thumbsup": "げんきな", "coffee": "のんびりやの", "dango": "たべしんぼうの",
            "guitar": "おんがくずきの", "sleep": "ねぼすけな"}
POSE_ITEM = {"thumbsup": "サムズアップ", "coffee": "コーヒー", "dango": "おだんご",
             "guitar": "ギター", "sleep": "リュック"}
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


def _sparkles(seed, n):
    """4つ角のキラキラを、背景の上に散らす（位置は入力から決まるので毎回同じ）"""
    r = random.Random(seed ^ 0x5EED)
    layer = Image.new("RGBA", (SIZE * 2, SIZE * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y = r.randint(200, SIZE - 200) * 2, r.randint(160, SIZE - 160) * 2
        a = r.randint(26, 58) * 2
        d.polygon([(x, y - a), (x + a * 0.28, y - a * 0.28), (x + a, y), (x + a * 0.28, y + a * 0.28),
                   (x, y + a), (x - a * 0.28, y + a * 0.28), (x - a, y), (x - a * 0.28, y - a * 0.28)],
                  fill=(255, 255, 255, 235))
    return layer.resize((SIZE, SIZE), Image.LANCZOS)


def _recolor_fur(body, fur_mask, rgb, vref=0.80):
    """体の絵のうち「毛」の部分（fur_mask）だけを、好きな色に差し替える。
    明るさは元の絵のまま使うので、濃い毛→濃い色、薄いおなか→薄い色になる。"""
    r, g, b, a = body.split()
    v = ImageChops.lighter(ImageChops.lighter(r, g), b)                       # 各ピクセルの明るさ
    new = Image.merge("RGB", [v.point(lambda x, c=c: min(255, int(c * min(x / (255 * vref), 1.12)))) for c in rgb])
    mixed = Image.composite(new, Image.merge("RGB", (r, g, b)), fur_mask)     # 毛の所だけ差し替え
    out = mixed.convert("RGBA"); out.putalpha(a)
    return out


def _poses(folder):
    return sorted(p for p in folder.glob("*.png") if not p.stem.endswith("_mask")) if folder.exists() else []


def _pose_pool(rarity):
    """その段階のポーズ。無ければ1つ下の段階から探す（★4の絵が未完成でも動く）"""
    for lv in range(rarity, 0, -1):
        files = _poses(CHARS / f"r{lv}")
        if files:
            return files
    return []


def _compose_pose(month, day, color, rng):
    """1枚絵モード：星の段階 → ポーズを選ぶ → リュックを好きな色に → 背景に重ねる"""
    r = rng.random()
    rarity = next((lv for th, lv in RARITY_STEPS if r < th), 1)
    if FORCE_RARITY in (1, 2, 3, 4):
        rarity = FORCE_RARITY
    pose = rng.choice(_pose_pool(rarity))
    bg = _pick(rng, "background")

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    if rarity == 4:
        canvas = Image.alpha_composite(canvas, _gold_background())
    elif bg:
        canvas = Image.alpha_composite(canvas, Image.open(bg).convert("RGBA"))
    if rarity >= 3:
        canvas = Image.alpha_composite(canvas, _sparkles(make_seed(month, day, color), 10 if rarity == 3 else 18))

    art = Image.open(pose).convert("RGBA")
    mask = pose.with_name(pose.stem + "_mask.png")
    if mask.exists():                                    # リュックだけ好きな色に（体の色は変えない）
        art = _recolor_fur(art, Image.open(mask).convert("L"), COLORS[color], vref=0.86)
    canvas = Image.alpha_composite(canvas, art)
    return canvas, {"background": bg, "pose": pose, "face": None, "outfit": None, "hat": None, "item": None}, rng, rarity


def compose_character(month, day, color):
    """入力 → (キャラ画像, 選ばれたパーツ, rng, レア度1〜4)。同じ入力なら必ず同じ結果。"""
    rng = random.Random(make_seed(month, day, color))
    if any(_poses(CHARS / f"r{lv}") for lv in range(1, 5)):
        return _compose_pose(month, day, color, rng)
    ch = {"background": _pick(rng, "background"), "face": _pick(rng, "face"),
          "outfit": _pick(rng, "outfit", 0.15), "hat": _pick(rng, "hat", 0.3),
          "item": _pick(rng, "item", 0.3)}
    r = rng.random()                     # レア度を決める（乱数の消費数は今までと同じ）
    rarity = next((lv for th, lv in RARITY_STEPS if r < th), 1)
    if FORCE_RARITY in (1, 2, 3, 4):
        rarity = FORCE_RARITY

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    if rarity == 4:
        canvas = Image.alpha_composite(canvas, _gold_background())      # ★4：金の背景
    elif ch["background"]:
        canvas = Image.alpha_composite(canvas, Image.open(ch["background"]).convert("RGBA"))
    if rarity >= 3:                                                      # ★3以上：キラキラを重ねる
        canvas = Image.alpha_composite(canvas, _sparkles(make_seed(month, day, color), 10 if rarity == 3 else 18))

    body = Image.open(PARTS / "body" / "base.png").convert("RGBA")
    fur_path = PARTS / "body" / "fur.png"
    if fur_path.exists():          # 本物の絵：毛の部分だけ色を差し替える（赤いリュック等はそのまま）
        canvas = Image.alpha_composite(canvas, _recolor_fur(body, Image.open(fur_path).convert("L"), COLORS[color]))
    else:                          # 仮の絵：白い体に色を掛ける
        tint = Image.new("RGBA", body.size, COLORS[color] + (255,))
        canvas = Image.alpha_composite(canvas, ImageChops.multiply(body, tint))
    for cat in ("face", "outfit", "hat", "item"):
        if ch[cat]:
            canvas = Image.alpha_composite(canvas, Image.open(ch[cat]).convert("RGBA"))
    return canvas, ch, rng, rarity


def make_fortune(ch, rng, color, rarity):
    stem = lambda k: ch[k].stem if ch[k] else None
    # 表情パーツが無い間は、診断名の形容詞を入力から決める
    pose = ch["pose"].stem if ch.get("pose") else None
    adj = FACE_ADJ.get(stem("face")) if ch["face"] else (POSE_ADJ.get(pose) or rng.choice(list(FACE_ADJ.values())))
    title = f"{HAT_NAME.get(stem('hat'), '')}{adj or 'ふしぎな'}きゅー太"
    return {"title": title, "message": rng.choice(MESSAGES), "lucky_color": color,
            "lucky_item": POSE_ITEM.get(pose) or ITEM_NAME.get(stem("item"), "ひみつ"),
            "rarity": rarity, "rare": rarity >= 4, "rarity_note": RARITY_NOTE[rarity]}


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


def make_sticker(char_img, name, title, number, save=True, rarity=1):
    """印刷用（60mm角・300dpi）のシール画像を作る。"""
    fp = find_font()
    s = PX
    sticker = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    big = Image.new("L", (s * 2, s * 2), 0)
    ImageDraw.Draw(big).rounded_rectangle((0, 0, s * 2 - 1, s * 2 - 1), radius=150, fill=255)
    sticker.paste((255, 255, 255, 255), (0, 0), big.resize((s, s), Image.LANCZOS))

    d = ImageDraw.Draw(sticker)
    bw = RARITY_BORDER[rarity]                                    # レア度で縁が太く・色付きになる
    bcol = (225, 225, 225) if rarity == 1 else RARITY_COLOR[rarity]
    d.rounded_rectangle((2, 2, s - 3, s - 3), radius=75, outline=bcol + (255,), width=bw)
    fs = ImageFont.truetype(fp, int(s * 0.075))                   # 左上に★
    d.text((bw + 16, bw + 8), "★" * rarity, font=fs, fill=RARITY_COLOR[rarity] + (255,))

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
