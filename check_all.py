"""素材チェック用：ランダムな組み合わせを一覧画像にして出力（変な組み合わせの目視確認）
使い方: python check_all.py 60   → check_sheet.png"""
import sys, random
from PIL import Image
import kyuta as K
n = int(sys.argv[1]) if len(sys.argv) > 1 else 48
cols, cell = 8, 200
sheet = Image.new("RGB", (cols * cell, ((n + cols - 1) // cols) * cell), (235, 235, 235))
colors = list(K.COLORS)
for i in range(n):
    im, *_ = K.compose_character(random.randint(1, 12), random.randint(1, 28), random.choice(colors))
    im = im.resize((cell, cell)); sheet.paste(im, ((i % cols) * cell, (i // cols) * cell), im)
sheet.save("check_sheet.png"); print("check_sheet.png を出力しました")
