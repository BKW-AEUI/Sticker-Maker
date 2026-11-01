"""実験用ログ：診断のたびに、Googleフォームへ1件送る（ブラウザ版用）。
・フォームの回答は、自動でスプレッドシートに溜まる（Google Cloudの設定は不要）
・Secrets（設定）が無いときは何もしない＝ログ無しでも普通に動く
・送信は裏で行い、失敗してもアプリは止めない（状態は ?debug=1 を付けたURLで見られる）
・名前は記録しない（企画書の「個人情報を扱わない」を守るため）
・フォームの質問は1つだけ。中身は「|」区切りで送る（シート側のSPLITで列に分ける）"""
import threading
from datetime import datetime, timedelta, timezone
import urllib.error
import urllib.parse
import urllib.request

import streamlit as st

JST = timezone(timedelta(hours=9))

# 送る項目の順番（シートで列に分けるときの見出し）
HEADERS = ["イベント", "セッション", "月", "日", "色", "★", "ポーズ", "小物", "診断名", "メモ"]
LAST = "まだ記録していません"      # ?debug=1 で表示される、直近の状態


def _config():
    """Secretsからフォームの送り先を読む。無ければ None（＝記録しない）"""
    try:
        if "form_url" in st.secrets and "form_entry" in st.secrets:
            return str(st.secrets["form_url"]), str(st.secrets["form_entry"])
    except Exception:                           # Secretsが何も登録されていないとき
        pass
    return None


def _clean(v):
    return str(v if v is not None else "").replace("|", "／").replace("\n", " ")[:200]


def _send(url, entry, text):
    """フォームに1件送る（裏の処理から呼ばれる）"""
    global LAST
    try:
        data = urllib.parse.urlencode({entry: text}).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST", headers={"User-Agent": "kyuta-log"})
        with urllib.request.urlopen(req, timeout=8) as r:
            LAST = f"OK {datetime.now(JST):%H:%M:%S}（送信 HTTP {r.status}）"
    except urllib.error.HTTPError as e:
        LAST = f"NG {datetime.now(JST):%H:%M:%S} HTTP {e.code}（フォームのURLか、ログイン不要の設定を確認）"
    except Exception as e:
        LAST = f"NG {datetime.now(JST):%H:%M:%S} {type(e).__name__}: {str(e)[:120]}"


def log(event, sid, month="", day="", color="", rarity="", pose="", acc="", title="", memo=""):
    """1件送る。event は「診断」「ダウンロード」「もういちど」「エラー」など。"""
    global LAST
    try:
        cfg = _config()
        if cfg is None:
            LAST = "設定なし（Secrets未登録）→ 記録しません"
            return None
        text = "|".join(_clean(v) for v in [event, sid, month, day, color, rarity, pose, acc or "なし", title, memo])
        LAST = "送信中…"                                   # 先に表示を変えておく（送信が先に終わっても上書きされない）
        t = threading.Thread(target=_send, args=(*cfg, text), daemon=True)   # 画面を待たせない
        t.start()
        return t
    except Exception as e:                      # ログの失敗でアプリを止めない
        LAST = f"NG {type(e).__name__}: {str(e)[:150]}"
        return None
