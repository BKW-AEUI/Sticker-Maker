# きゅー太しんだん

誕生日と好きな色から、きゅー太があなたを診断して、名前入りのシールを作るデモ（ローカル完結・ネット不使用）。

## 動かし方（Windows）
```
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pygame-ce pillow
.\.venv\Scripts\python.exe make_placeholders.py   # 背景の仮素材を作る（初回のみ）
.\.venv\Scripts\python.exe main.py                # 起動（本番は --fullscreen）
```
- 終了は Ctrl+Q。60秒放置でタイトルへ戻る。
- 完成したシールは `output/`（60mm角・300dpi）に番号つきで保存される。
- exe化は `build.bat`（USBに入れて持ち運べる）。

## しくみ
- 誕生日と色から数字を作り、その数字でくじ引き → 同じ入力なら同じ結果。
- 星の段階（★1〜★4）→ ポーズ（assets/chars/r1〜r4）→ リュックの色（好きな色）→ 背景 → 頭の小物（お花）の順に決まる。
- ★が多いほど、レアなポーズと小物が出やすい。

## 素材の足し方
- ポーズ: `python prepare_pose.py 絵.png 段階(1〜4) 名前`（要 numpy, scipy）。頭の位置を `assets/chars/heads.json` に書くと小物が付く。
- 診断名・ラッキーアイテムは `kyuta.py` の POSE_ADJ / POSE_ITEM に1行足す。
- 確率は `kyuta.py` の RARITY_STEPS / ACC_NONE。

## ブラウザ版
`streamlit_app.py`（承認用の簡易版）。Streamlit Community Cloud にデプロイして使う。

## ファイル
kyuta.py（ロジック）/ main.py（画面）/ streamlit_app.py（ブラウザ版）/ prepare_pose.py（素材変換）/ make_placeholders.py（仮素材）/ check_all.py（確認用）
