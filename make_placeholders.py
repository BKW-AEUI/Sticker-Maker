"""仮パーツ生成。本物のイラストができたら assets/parts/ の各フォルダのPNGを差し替えるだけ。
（全パーツ 1024x1024・透過PNG・きゅー太の正しい位置に描いた状態で書き出す）"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageFilter

S, K = 1024, 2   # K: 2倍で描いて縮小（ジャギー対策）
OUT = Path(__file__).parent / "assets" / "parts"
BK = (40, 40, 40, 255)


class D:
    def __init__(self):
        self.im = Image.new("RGBA", (S * K, S * K), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
    def _s(self, v): return [x * K for x in v] if isinstance(v, (list, tuple)) and not isinstance(v[0], (list, tuple)) else [(x * K, y * K) for x, y in v]
    def ellipse(self, b, fill=None, ol=None, w=0): self.d.ellipse(self._s(b), fill=fill, outline=ol, width=w * K)
    def poly(self, p, fill=None, ol=None, w=0):
        self.d.polygon(self._s(p), fill=fill)
        if ol: self.d.line(self._s(p + [p[0]]), fill=ol, width=w * K, joint="curve")
    def rect(self, b, fill=None, ol=None, w=0, r=0): self.d.rounded_rectangle(self._s(b), radius=r * K, fill=fill, outline=ol, width=w * K)
    def arc(self, b, a0, a1, fill=BK, w=10): self.d.arc(self._s(b), a0, a1, fill=fill, width=w * K)
    def pie(self, b, a0, a1, fill=None, ol=None, w=0): self.d.pieslice(self._s(b), a0, a1, fill=fill, outline=ol, width=w * K)
    def line(self, p, fill=BK, w=10): self.d.line(self._s(p), fill=fill, width=w * K, joint="curve")
    def out(self): return self.im.resize((S, S), Image.LANCZOS)


def save(img, cat, name):
    p = OUT / cat; p.mkdir(parents=True, exist_ok=True); img.save(p / f"{name}.png")


def circle_mask():
    m = Image.new("L", (S * K, S * K), 0)
    ImageDraw.Draw(m).ellipse((40 * K, 40 * K, (S - 40) * K, (S - 40) * K), fill=255)
    return m.resize((S, S), Image.LANCZOS)


def backgrounds():
    specs = [("bg01", (255, 244, 190), "plain"), ("bg02", (200, 230, 255), "dots"),
             ("bg03", (255, 215, 230), "stripes"), ("bg04", (210, 240, 210), "stars")]
    for name, col, kind in specs:
        d = D(); d.ellipse((0, 0, S, S), fill=col + (255,))
        if kind == "dots":
            for y in range(120, S, 140):
                for x in range(120 + (y // 140 % 2) * 70, S, 140): d.ellipse((x - 18, y - 18, x + 18, y + 18), fill=(255, 255, 255, 200))
        if kind == "stripes":
            for i in range(-S, S * 2, 110): d.line([(i, 0), (i - 500, S)], fill=(255, 255, 255, 170), w=45)
        if kind == "stars":
            for cx, cy in [(180, 260), (800, 200), (860, 700), (230, 760), (520, 120)]:
                pts = [(cx + (40 if i % 2 == 0 else 17) * math.cos(i * math.pi / 5 - math.pi / 2),
                        cy + (40 if i % 2 == 0 else 17) * math.sin(i * math.pi / 5 - math.pi / 2)) for i in range(10)]
                d.poly(pts, fill=(255, 255, 255, 230))
        im = d.out(); im.putalpha(ImageChops.darker(im.getchannel("A"), circle_mask()))
        save(im, "background", name)


def body():
    d = D()
    for b in [(335, 800, 460, 885), (564, 800, 689, 885), (205, 540, 330, 640), (694, 540, 819, 640)]:
        d.ellipse(b, fill=(255, 255, 255, 255), ol=BK, w=14)
    d.ellipse((262, 300, 762, 850), fill=(255, 255, 255, 255), ol=BK, w=14)
    save(d.out(), "body", "base")


def faces():
    def eyes_dot(d): [d.ellipse((x - 20, 500, x + 20, 560), fill=BK) for x in (420, 604)]
    def eyes_arc_up(d): [d.arc((x - 38, 495, x + 38, 565), 200, 340, w=12) for x in (420, 604)]
    d = D(); eyes_dot(d); d.pie((462, 560, 562, 650), 0, 180, fill=(220, 90, 90, 255), ol=BK, w=8); save(d.out(), "face", "face01")
    d = D(); [d.arc((x - 38, 515, x + 38, 575), 20, 160, w=12) for x in (420, 604)]; d.ellipse((492, 590, 532, 625), fill=BK); save(d.out(), "face", "face02")
    d = D(); eyes_arc_up(d); d.arc((452, 540, 572, 640), 20, 160, w=12); save(d.out(), "face", "face03")
    d = D(); d.line([(385, 490), (440, 525), (385, 560)], w=13); d.line([(639, 490), (584, 525), (639, 560)], w=13)
    d.pie((462, 565, 562, 640), 0, 180, fill=(220, 90, 90, 255), ol=BK, w=8); d.ellipse((495, 610, 530, 655), fill=(255, 140, 150, 255), ol=BK, w=6); save(d.out(), "face", "face04")
    d = D(); eyes_dot(d); [d.ellipse((x - 42, 570, x + 42, 615), fill=(255, 150, 160, 190)) for x in (380, 644)]; d.arc((482, 585, 542, 625), 20, 160, w=10); save(d.out(), "face", "face05")


def clipped(draw_fn, name, cat="outfit"):
    base = Image.open(OUT / "body" / "base.png").getchannel("A").filter(ImageFilter.MinFilter(31))
    d = D(); draw_fn(d); im = d.out(); im.putalpha(ImageChops.darker(im.getchannel("A"), base)); save(im, cat, name)


def outfits():
    def stripes(d):
        for i, y in enumerate(range(640, 850, 60)): d.rect((200, y, 830, y + 30), fill=(255, 90, 90, 255) if i % 2 == 0 else (255, 255, 255, 0))
    def bib(d): d.rect((380, 650, 644, 900), fill=(255, 200, 70, 255), ol=BK, w=8, r=30); d.ellipse((480, 710, 544, 774), fill=(255, 255, 255, 255))
    def scarf(d): d.rect((280, 630, 744, 700), fill=(220, 60, 70, 255), ol=BK, w=8, r=30); d.rect((620, 690, 690, 790), fill=(220, 60, 70, 255), ol=BK, w=8, r=20)
    def overalls(d): d.rect((200, 700, 830, 900), fill=(80, 130, 220, 255)); [d.rect((x, 620, x + 30, 720), fill=(80, 130, 220, 255)) for x in (360, 634)]
    def dots(d): [d.ellipse((x - 20, y - 20, x + 20, y + 20), fill=(120, 80, 200, 255)) for x, y in [(350, 700), (450, 760), (560, 690), (670, 760), (400, 820), (620, 830), (510, 650)]]
    for n, f in enumerate([stripes, bib, scarf, overalls, dots], 1): clipped(f, f"outfit0{n}")


def hats():
    def party(d): d.poly([(430, 335), (594, 335), (512, 120)], fill=(255, 120, 170, 255), ol=BK, w=10); d.ellipse((482, 90, 542, 150), fill=(255, 230, 90, 255), ol=BK, w=8)
    def cap(d): d.pie((382, 190, 642, 450), 180, 360, fill=(255, 205, 70, 255), ol=BK, w=10); d.rect((400, 315, 700, 345), fill=(255, 205, 70, 255), ol=BK, w=10, r=14)
    def crown(d): d.poly([(390, 330), (390, 200), (450, 260), (512, 170), (574, 260), (634, 200), (634, 330)], fill=(255, 215, 60, 255), ol=BK, w=10); d.ellipse((492, 270, 532, 310), fill=(230, 60, 80, 255))
    def chef(d): [d.ellipse(b, fill=(255, 255, 255, 255), ol=BK, w=10) for b in [(390, 160, 520, 290), (504, 160, 634, 290), (447, 110, 577, 240)]]; d.rect((410, 270, 614, 345), fill=(255, 255, 255, 255), ol=BK, w=10, r=12)
    def ribbon(d): d.poly([(640, 350), (740, 290), (740, 410)], fill=(230, 60, 80, 255), ol=BK, w=10); d.poly([(640, 350), (540, 290), (540, 410)], fill=(230, 60, 80, 255), ol=BK, w=10); d.ellipse((610, 320, 670, 380), fill=(255, 120, 130, 255), ol=BK, w=10)
    for n, f in enumerate([party, cap, crown, chef, ribbon], 1):
        d = D(); f(d); save(d.out(), "hat", f"hat0{n}")


def items():
    def balloon(d): d.line([(800, 620), (830, 480)], fill=(90, 90, 90, 255), w=6); d.ellipse((770, 280, 900, 440), fill=(255, 90, 100, 255), ol=BK, w=9)
    def star(d):
        pts = [(830 + (80 if i % 2 == 0 else 34) * math.cos(i * math.pi / 5 - math.pi / 2), 520 + (80 if i % 2 == 0 else 34) * math.sin(i * math.pi / 5 - math.pi / 2)) for i in range(10)]
        d.poly(pts, fill=(255, 225, 60, 255), ol=BK, w=9)
    def flower(d):
        d.line([(780, 640), (830, 740)], fill=(60, 160, 80, 255), w=10)
        for k in range(6):
            a = k * math.pi / 3; cx, cy = 800 + 42 * math.cos(a), 540 + 42 * math.sin(a); d.ellipse((cx - 32, cy - 32, cx + 32, cy + 32), fill=(255, 150, 200, 255), ol=BK, w=6)
        d.ellipse((772, 512, 828, 568), fill=(255, 220, 60, 255), ol=BK, w=6)
    def heart(d): d.ellipse((760, 460, 840, 540), fill=(240, 70, 100, 255)); d.ellipse((820, 460, 900, 540), fill=(240, 70, 100, 255)); d.poly([(764, 510), (896, 510), (830, 620)], fill=(240, 70, 100, 255))
    def icecream(d): d.poly([(775, 520), (865, 520), (820, 660)], fill=(230, 180, 110, 255), ol=BK, w=8); d.ellipse((770, 430, 870, 530), fill=(255, 170, 200, 255), ol=BK, w=8); d.ellipse((785, 380, 855, 450), fill=(255, 250, 230, 255), ol=BK, w=8)
    for n, f in enumerate([balloon, star, flower, heart, icecream], 1):
        d = D(); f(d); save(d.out(), "item", f"item0{n}")


if __name__ == "__main__":
    backgrounds(); body(); faces(); outfits(); hats(); items()
    print("仮パーツを生成しました:", OUT)
