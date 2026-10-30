"""スタンプなどの絵を、デモ用の素材に変換する道具。
使い方:  python prepare_pose.py 絵.png 段階(1〜4) [名前]
  例:    python prepare_pose.py guitar.png 3 guitar
できるもの:
  assets/chars/r3/guitar.png       背景を透明にして、1024x1024の中央に配置した絵
  assets/chars/r3/guitar_mask.png  リュックの色替えをする範囲（白い所）
必要な部品:  pip install numpy scipy pillow"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

ROOT = Path(__file__).parent


def to_rgba(im):
    """背景が透明ならそのまま。白い背景なら、外側とつながった白だけを透明にする。"""
    im = im.convert("RGBA")
    if np.array(im.getchannel("A")).min() < 250:
        return im
    a = np.array(im.convert("RGB")).astype(np.int32)
    mx, mn = a.max(2), a.min(2)
    lab, _ = ndi.label((mn > 205) & ((mx - mn) < 22))
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = ndi.binary_dilation(np.isin(lab, list(edge)), iterations=1)
    alpha = np.array(Image.fromarray(np.where(bg, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)))
    return Image.fromarray(np.dstack([a.astype(np.uint8), alpha]), "RGBA")


def fit(im, maxw=880, maxh=840, max_up=2.0):
    """絵の余白を切って、1024x1024の中央に置く（小さい絵を拡大しすぎない）"""
    box = im.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox()
    c = im.crop(box)
    sc = min(maxw / c.width, maxh / c.height, max_up)
    c = c.resize((round(c.width * sc), round(c.height * sc)), Image.LANCZOS)
    cv = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    cv.paste(c, ((1024 - c.width) // 2, max(60, (1024 - c.height) // 2 + 20)), c)
    return cv


def backpack_mask(img):
    """赤くて大きな塊＝リュック。ほっぺ・口など小さい赤やピンクは除く。"""
    arr = np.array(img).astype(np.float32)
    rgb = arr[..., :3] / 255
    mx, mn = rgb.max(2), rgb.min(2)
    d = np.maximum(mx - mn, 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    red = ((hue < 14) | (hue > 345)) & (sat > 0.60) & (mx > 0.30) & (arr[..., 3] > 0)
    lab, n = ndi.label(red)
    keep = np.zeros_like(red)
    for i in range(1, n + 1):
        if (lab == i).sum() > 1200:
            keep |= lab == i
    return ndi.binary_dilation(keep, iterations=2) & (arr[..., 3] > 0) & (sat > 0.25)


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    src, tier = Path(sys.argv[1]), int(sys.argv[2])
    name = sys.argv[3] if len(sys.argv) > 3 else src.stem
    out = ROOT / "assets" / "chars" / f"r{tier}"
    out.mkdir(parents=True, exist_ok=True)
    img = fit(to_rgba(Image.open(src)))
    img.save(out / f"{name}.png")
    mask = backpack_mask(img)
    Image.fromarray((mask * 255).astype(np.uint8), "L").save(out / f"{name}_mask.png")
    print(f"できました: {out / (name + '.png')}（リュック判定 {int(mask.sum())}px）")


if __name__ == "__main__":
    main()
