# きゅー太しんだん デモ

## 動かし方（Windows / Mac 共通）
```
pip install pygame pillow
python make_placeholders.py   # 仮パーツ生成（初回のみ。本物の素材ができたら不要）
python main.py                # ウィンドウで起動（本番は --fullscreen）
```
- 完成したシールは `output/` に 60mm角・300dpi のPNGで保存されます（番号つき）
- 終了は Ctrl+Q（ESCでは終了しません）／60秒放置で自動的にタイトルへ戻ります
- 日本語フォントは `assets/fonts/` に TTF/OTF を入れると優先使用。無ければWindows標準フォント(メイリオ等)を使います

## 素材の差し替え
`assets/parts/` の各フォルダ（background / body / face / outfit / hat / item）のPNGを差し替えるだけ。
全パーツ 1024x1024・透過・きゅー太の正しい位置に描いた状態で書き出す。
body/base.png は「白塗り＋黒線」（色は好きな色で自動で乗算）。
パーツを足したら kyuta.py の FACE_ADJ / HAT_NAME / ITEM_NAME に表示名を1行追加。

## ファイル
- kyuta.py … 診断・合成・シール生成（画面なしで単体利用可）
- main.py … 画面（タイトル→誕生日→色→名前→診断→シール）
- check_all.py … 組み合わせ一覧画像で目視チェック
