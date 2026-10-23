"""きゅー太しんだん デモ（ローカル完結・ネット不使用）
起動:  python main.py            （ウィンドウ）
       python main.py --fullscreen（本番用）
スタッフ操作: Ctrl+Q で終了 / ESCでは終了しません"""
import sys, os, math, time
import pygame
from PIL import Image
import kyuta as K

W, H = 1280, 720
IDLE_SEC = 60
CREAM, ORANGE, BROWN, WHITE = (255, 248, 225), (255, 165, 70), (90, 60, 40), (255, 255, 255)

# ---- 50音キーボード（カラオケ風：右から左へ あ行・か行…） ----
ROWS = ["あかさたなはまやらわ", "いきしちにひみ　り　", "うくすつぬふむゆるを", "えけせてねへめ　れ　", "おこそとのほもよろん"]
GRID = [[r[9 - c] for r in ROWS] for c in range(10)]  # GRID[col][row]、col0が左端（わ行）
def _m(a, b): return dict(zip(a, b))
DAKU = {**_m("かきくけこさしすせそたちつてとはひふへほ", "がぎぐげござじずぜぞだぢづでどばびぶべぼ")}
DAKU.update({v: k for k, v in list(DAKU.items())})
DAKU.update(_m("ぱぴぷぺぽ", "ばびぶべぼ"))
HANDAKU = {**_m("はひふへほ", "ぱぴぷぺぽ"), **_m("ぱぴぷぺぽ", "はひふへほ"), **_m("ばびぶべぼ", "ぱぴぷぺぽ")}
SMALL = _m("あいうえおつやゆよわ", "ぁぃぅぇぉっゃゅょゎ"); SMALL.update({v: k for k, v in list(SMALL.items())})


class App:
    def __init__(self, fullscreen=False):
        pygame.init()
        flags = pygame.SCALED | (pygame.FULLSCREEN if fullscreen else 0)
        self.screen = pygame.display.set_mode((W, H), flags)
        pygame.display.set_caption("きゅー太しんだん")
        self.font_path = K.find_font()
        self._fonts = {}
        self.clock = pygame.time.Clock()
        self.buttons = []
        self.sample = self._surf(K.compose_character(6, 15, "ピンク")[0], 380)
        self.reset()

    # ---------- 状態 ----------
    def reset(self):
        self.month = self.day = self.color = None
        self.name = ""
        self.go("title")

    def go(self, state):
        self.state, self.t = state, 0.0
        self.last_input = time.time()

    # ---------- 描画ヘルパー ----------
    def font(self, size):
        if size not in self._fonts: self._fonts[size] = pygame.font.Font(self.font_path, size)
        return self._fonts[size]

    def text(self, s, size, color=BROWN, center=None, topleft=None, alpha=255):
        surf = self.font(size).render(s, True, color)
        if alpha < 255: surf.set_alpha(alpha)
        r = surf.get_rect(); 
        if center: r.center = center
        if topleft: r.topleft = topleft
        self.screen.blit(surf, r); return r

    def button(self, rect, label, fill=ORANGE, size=40, enabled=True, bid=None, fg=WHITE):
        rect = pygame.Rect(rect); bid = bid if bid is not None else label
        hover = enabled and rect.collidepoint(pygame.mouse.get_pos())
        col = (150, 150, 150) if not enabled else tuple(min(255, c + 25) for c in fill) if hover else fill
        pygame.draw.rect(self.screen, tuple(max(0, c - 70) for c in col), rect.move(0, 6), border_radius=18)
        pygame.draw.rect(self.screen, col, rect, border_radius=18)
        self.text(label, size, fg, center=rect.center)
        self.buttons.append((rect, bid, enabled))

    def _surf(self, pil, size):
        pil = pil.resize((size, size), Image.LANCZOS)
        return pygame.image.fromstring(pil.tobytes(), pil.size, "RGBA").convert_alpha()

    def title_bar(self, s):
        self.text(s, 64, BROWN, center=(W // 2, 70))

    def back(self, to):
        self.button((20, 20, 150, 56), "もどる", (150, 130, 110), 28, bid=("back", to))

    # ---------- フレーム ----------
    def step(self, dt):
        self.t += dt
        self.screen.fill(CREAM)
        self.buttons = []
        getattr(self, "draw_" + self.state)()
        pygame.display.flip()
        if self.state != "title" and time.time() - self.last_input > IDLE_SEC:
            self.reset()   # 放置されたら自動でタイトルへ（次の子がすぐ使える）

    def click(self, bid):   # クリック処理（テストからも使う）
        for rect, b, en in self.buttons:
            if b == bid and en: self.on_click(b); return True
        return False

    def on_click(self, b):
        self.last_input = time.time()
        if isinstance(b, tuple) and b[0] == "back": self.go(b[1]); return
        getattr(self, "click_" + self.state)(b)

    def handle(self, ev):
        if ev.type == pygame.QUIT: return False
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_q and ev.mod & pygame.KMOD_CTRL: return False
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.last_input = time.time()
            for rect, b, en in self.buttons:
                if en and rect.collidepoint(ev.pos): self.on_click(b); break
        return True

    # ---------- 各画面 ----------
    def draw_title(self):
        bounce = abs(math.sin(self.t * 3)) * 28
        self.screen.blit(self.sample, (W // 2 - 190, 150 - bounce))
        self.text("きゅー太 しんだん", 92, ORANGE, center=(W // 2, 90))
        self.text("たんじょうびと すきないろで  きみだけの きゅー太を つくろう！", 34, BROWN, center=(W // 2, 560))
        self.button((W // 2 - 180, 600, 360, 90), "スタート！", ORANGE, 52, bid="start")

    def click_title(self, b): self.go("month")

    def draw_month(self):
        self.back("title"); self.title_bar("なんがつ うまれ？")
        for i in range(12):
            x, y = 100 + (i % 6) * 190, 220 + (i // 6) * 170
            self.button((x, y, 170, 140), f"{i + 1}がつ", (255, 150, 90) if i % 2 else (255, 190, 80), 48, bid=i + 1)

    def click_month(self, b): self.month = b; self.go("day")

    def draw_day(self):
        self.back("month"); self.title_bar(f"{self.month}がつ なんにち？")
        maxd = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][self.month - 1]
        for i in range(31):
            x, y = 80 + (i % 8) * 140, 150 + (i // 8) * 125
            self.button((x, y, 125, 105), f"{i + 1}", (110, 190, 230) if i % 2 else (90, 170, 220), 46, enabled=i < maxd, bid=i + 1)

    def click_day(self, b): self.day = b; self.go("color")

    def draw_color(self):
        self.back("day"); self.title_bar("すきな いろは？")
        for i, (name, rgb) in enumerate(K.COLORS.items()):
            cx, cy = 240 + (i % 4) * 267, 270 + (i // 4) * 220
            pygame.draw.circle(self.screen, tuple(c - 60 for c in rgb), (cx, cy + 6), 82)
            pygame.draw.circle(self.screen, rgb, (cx, cy), 82)
            pygame.draw.circle(self.screen, WHITE, (cx - 28, cy - 28), 16)
            self.text(name, 36, BROWN, center=(cx, cy + 112))
            self.buttons.append((pygame.Rect(cx - 90, cy - 90, 180, 200), name, True))

    def click_color(self, b): self.color = b; self.go("name")

    def draw_name(self):
        self.back("color"); self.text("おなまえを いれてね（6もじまで）", 44, BROWN, center=(W // 2, 56))
        for i in range(K.NAME_MAX):   # 文字スロット
            r = pygame.Rect(W // 2 - 3 * 100 + i * 100 + 5, 92, 90, 84)
            pygame.draw.rect(self.screen, WHITE, r, border_radius=14)
            pygame.draw.rect(self.screen, ORANGE if i == len(self.name) else (220, 210, 190), r, 4, border_radius=14)
            if i < len(self.name): self.text(self.name[i], 54, BROWN, center=r.center)
        full = len(self.name) >= K.NAME_MAX
        for c in range(10):
            for r in range(5):
                ch = GRID[c][r]
                if ch != "　":
                    self.button((104 + c * 108, 200 + r * 76, 100, 68), ch, (140, 190, 120) if (c + r) % 2 else (120, 175, 105),
                                44, enabled=not full, bid=("ch", ch))
        y = 200 + 5 * 76 + 12
        for i, (lab, bid) in enumerate([("゛", "daku"), ("゜", "handaku"), ("小", "small"), ("ー", ("ch", "ー"))]):
            self.button((104 + i * 108, y, 100, 68), lab, (230, 150, 70), 40, enabled=(bid != ("ch", "ー") or not full), bid=bid)
        self.button((104 + 4 * 108, y, 150, 68), "けす", (210, 110, 110), 36, enabled=bool(self.name), bid="del")
        self.button((104 + 4 * 108 + 158, y, 200, 68), "ぜんぶけす", (190, 90, 90), 32, enabled=bool(self.name), bid="clear")
        self.button((1176 - 250, y, 250, 68), "おわり！", (255, 150, 40), 44, enabled=bool(self.name), bid="ok")

    def click_name(self, b):
        n = self.name
        if isinstance(b, tuple) and b[0] == "ch": self.name = n + b[1] if len(n) < K.NAME_MAX else n
        elif b == "del": self.name = n[:-1]
        elif b == "clear": self.name = ""
        elif b in ("daku", "handaku", "small") and n:
            table = {"daku": DAKU, "handaku": HANDAKU, "small": SMALL}[b]
            self.name = n[:-1] + table.get(n[-1], n[-1])
        elif b == "ok":
            self.char_img, self.chosen, rng, rare = K.compose_character(self.month, self.day, self.color)
            self.fortune = K.make_fortune(self.chosen, rng, self.color, rare)
            self.char_surf = self._surf(self.char_img, 460)
            self.go("loading")

    def draw_loading(self):
        self.text("きゅー太が しんだんちゅう" + "." * (int(self.t * 3) % 4), 56, BROWN, center=(W // 2, 220))
        cx, cy = W // 2, 410
        for i in range(8):
            a = self.t * 4 + i * math.tau / 8
            r = 14 + 8 * math.sin(self.t * 6 + i)
            pygame.draw.circle(self.screen, (255, 200 - i * 12, 80 + i * 10), (cx + 110 * math.cos(a), cy + 110 * math.sin(a)), r)
        self.text("ドキドキ…", 44, ORANGE, center=(cx, cy))
        if self.t > 2.4: self.go("result")

    def draw_result(self):
        t, f = self.t, self.fortune
        if f["rare"] and int(t * 6) % 2 == 0 and t < 3:
            pygame.draw.rect(self.screen, (255, 245, 170), (0, 0, W, H))
        pop = min(1, t / 0.5); size = int(460 * (0.6 + 0.4 * pop))
        bounce = abs(math.sin(t * 2.5)) * 16 if t > 0.6 else 0
        s = pygame.transform.smoothscale(self.char_surf, (size, size))
        self.screen.blit(s, (60 + (460 - size) // 2, 130 + (460 - size) // 2 - bounce))
        x = 580
        self.text(f"{self.name}は…", 40, BROWN, topleft=(x, 70), alpha=int(255 * min(1, t / 0.4)))
        if t > 0.7:
            self.text(f["title"] + "！" if not f["rare"] else f["title"], 48 if len(f["title"]) < 14 else 38,
                      (255, 120, 40) if not f["rare"] else (230, 150, 0), topleft=(x, 130))
        if t > 1.5:
            a = int(255 * min(1, (t - 1.5) / 0.6))
            words, line, y = f["message"], "", 230   # 折り返し
            for ch in words:
                if self.font(34).size(line + ch)[0] > 640: self.text(line, 34, BROWN, topleft=(x, y), alpha=a); line, y = "", y + 48
                line += ch
            self.text(line, 34, BROWN, topleft=(x, y), alpha=a)
        if t > 2.4:
            a = int(255 * min(1, (t - 2.4) / 0.6))
            self.text("ラッキーカラー", 30, (150, 120, 100), topleft=(x, 400), alpha=a)
            pygame.draw.circle(self.screen, K.COLORS[f["lucky_color"]], (x + 230, 418), 18)
            self.text(f["lucky_color"], 34, BROWN, topleft=(x + 260, 400), alpha=a)
            self.text("ラッキーアイテム", 30, (150, 120, 100), topleft=(x, 460), alpha=a)
            self.text(f["lucky_item"], 34, BROWN, topleft=(x + 260, 460), alpha=a)
        if t > 3.0:
            self.button((x, 560, 640, 100), "シールを つくる！", (255, 150, 40), 52, bid="make")

    def click_result(self, b):
        self.number = K.next_number()
        self.sticker, self.sticker_path = K.make_sticker(self.char_img, self.name, self.fortune["title"], self.number)
        self.sticker_surf = self._surf(self.sticker, 380)
        self.go("done")

    def draw_done(self):
        self.text("できたよ！", 84, ORANGE, center=(W // 2, 80))
        pygame.draw.rect(self.screen, WHITE, (100, 150, 420, 420), border_radius=24)
        self.screen.blit(self.sticker_surf, (120, 170))
        self.text("きみの ばんごうは", 40, BROWN, center=(860, 220))
        self.text(f"{self.number}", 190, (255, 130, 40), center=(860, 360))
        self.text("スタッフさんに ばんごうを", 36, BROWN, center=(860, 500))
        self.text("つたえて、シールを うけとってね！", 36, BROWN, center=(860, 550))
        self.button((W // 2 - 140, 610, 280, 80), "おわる", (150, 130, 110), 44, bid="end")
        if self.t > 25: self.reset()   # 自動でタイトルへ

    def click_done(self, b): self.reset()

    def run(self):
        running = True
        while running:
            for ev in pygame.event.get():
                running = self.handle(ev) and running
            self.step(self.clock.tick(60) / 1000)
        pygame.quit()


if __name__ == "__main__":
    App(fullscreen="--fullscreen" in sys.argv).run()
