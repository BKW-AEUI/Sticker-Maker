"""きゅー太しんだん（ブラウザ版・承認用デモ）
診断・合成・シール生成は kyuta.py をそのまま使用。画面だけStreamlitで作っています。
起動: streamlit run streamlit_app.py"""
import io, time
import streamlit as st
import kyuta as K

st.set_page_config(page_title="きゅー太しんだん", page_icon="🔮", layout="centered")

EMOJI = {"あか": "🔴", "オレンジ": "🟠", "きいろ": "🟡", "みどり": "🟢",
         "みずいろ": "🩵", "あお": "🔵", "むらさき": "🟣", "ピンク": "🌸"}
DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


@st.cache_resource
def ensure_parts():
    """素材フォルダが無ければ仮パーツを自動生成（本物の素材を置けばそちらを使う）"""
    if not (K.PARTS / "body" / "base.png").exists():
        import make_placeholders as mp
        mp.backgrounds(); mp.body(); mp.faces(); mp.outfits(); mp.hats(); mp.items()
    return True


ensure_parts()

st.markdown("""
<style>
.block-container {max-width: 760px; padding-top: 2rem;}
h1 {text-align:center; color:#ff9f43;}
.sub {text-align:center; color:#8a6a4a; margin-bottom:1.2rem;}
.title-big {font-size:2rem; font-weight:800; color:#ff7a28; text-align:center; margin:.4rem 0;}
.msg {font-size:1.2rem; text-align:center; padding:.8rem; background:#fff7e0; border-radius:14px;}
.rare {text-align:center; font-size:1.4rem; font-weight:800; color:#e0a000;}
</style>
""", unsafe_allow_html=True)

st.title("🔮 きゅー太 しんだん")
st.markdown('<div class="sub">たんじょうびと すきないろで、きみだけの きゅー太を つくろう！</div>', unsafe_allow_html=True)

res = st.session_state.get("result")

if res is None:
    month_label = st.pills("① なんがつ うまれ？", [f"{i}がつ" for i in range(1, 13)], key="month")
    month = int(month_label[:-2]) if month_label else None

    if month:
        day_label = st.pills("② なんにち？", [f"{i}" for i in range(1, DAYS[month - 1] + 1)], key=f"day_{month}")
        day = int(day_label) if day_label else None
    else:
        st.caption("② なんにち？（先に月をえらんでね）"); day = None

    color_label = st.pills("③ すきな いろは？", [f"{EMOJI[c]} {c}" for c in K.COLORS], key="color")
    color = color_label.split(" ", 1)[1] if color_label else None

    name = st.text_input(f"④ おなまえ（{K.NAME_MAX}もじまで・ニックネームでOK）", max_chars=K.NAME_MAX, key="name")
    st.caption("※ 本名・顔写真は使いません。誕生日は年を聞かず、保存もしません。")

    ready = bool(month and day and color and name.strip())
    if st.button("✨ しんだん する！", type="primary", disabled=not ready, width="stretch"):
        bar = st.progress(0, text="きゅー太が しんだんちゅう…")
        for i in range(12):
            time.sleep(0.15); bar.progress((i + 1) / 12, text="きゅー太が しんだんちゅう…" + "." * (i % 4))
        img, ch, rng, rare = K.compose_character(month, day, color)
        fortune = K.make_fortune(ch, rng, color, rare)
        sticker, _ = K.make_sticker(img, name.strip(), fortune["title"], 0, save=False)  # 保存しない
        buf = io.BytesIO(); sticker.save(buf, format="PNG", dpi=(K.DPI, K.DPI))
        st.session_state.result = {"img": img, "fortune": fortune, "name": name.strip(),
                                   "sticker": sticker, "png": buf.getvalue()}
        st.rerun()
    if not ready:
        st.caption("①〜④ ぜんぶ えらぶと ボタンが おせるよ")
else:
    f = res["fortune"]
    if f["rare"]:
        st.balloons()
        st.markdown('<div class="rare">✨ スーパーレア！ ✨</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center">{res["name"]} は…</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="title-big">{f["title"].replace("スーパーレア！", "")}！</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1], vertical_alignment="center")
    c1.image(res["img"], width="stretch")
    with c2:
        st.markdown(f'<div class="msg">{f["message"]}</div>', unsafe_allow_html=True)
        st.write("")
        st.markdown(f"**ラッキーカラー**　{EMOJI[f['lucky_color']]} {f['lucky_color']}")
        st.markdown(f"**ラッキーアイテム**　{f['lucky_item']}")

    st.divider()
    st.subheader("できあがりの シール")
    s1, s2 = st.columns([1, 1], vertical_alignment="center")
    s1.image(res["sticker"], width="stretch")
    with s2:
        st.caption("60mm角・300dpi の印刷用データです。本番ではこれをスタッフが印刷して手渡しします。")
        st.download_button("⬇ シールを ダウンロード", res["png"], file_name="kyuta_sticker.png",
                           mime="image/png", width="stretch")
    if st.button("🔁 もういちど つくる", width="stretch"):
        for k in ("result", "month", "color", "name"): st.session_state.pop(k, None)
        st.rerun()
