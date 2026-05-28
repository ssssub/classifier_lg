"""LG 냉장고 온라인 상담 — 베스트샵 매니저 경험을 웹에서.
Streamlit 앱. Replit에서 그대로 실행됨.
"""
import streamlit as st
from data_loader import load_products, SOFT_FEATURES
import engine as E

st.set_page_config(page_title="LG 냉장고 상담 매니저", page_icon="❄️", layout="centered")

# ── 약간의 스타일 ──
st.markdown("""
<style>
.block-container {max-width: 760px; padding-top: 2rem;}
.manager-bubble {
  background:#f4f1fb; border:1px solid #e3def5; border-radius:14px;
  padding:16px 18px; margin:8px 0 20px; font-size:1.05rem; line-height:1.5;
}
.manager-bubble b {color:#5a3fb8;}
.crumbs {color:#8a8a8a; font-size:.82rem; margin-bottom:.4rem;}
.rec-card {
  border:1px solid #e0e0e0; border-radius:16px; padding:20px 22px; margin:10px 0;
  background:#ffffff;
}
.rec-card.top {border:2px solid #a4133c; background:#fff7f8;}
.price {font-size:1.35rem; font-weight:700; color:#a4133c;}
.chip {display:inline-block; background:#eef; border-radius:999px;
  padding:2px 10px; margin:2px 4px 2px 0; font-size:.8rem; color:#445;}
.spec {color:#555; font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

PRODUCTS = load_products()

if "answers" not in st.session_state:
    st.session_state.answers = {}
ans = st.session_state.answers


def reset():
    st.session_state.answers = {}


def crumbs():
    """지금까지 답한 내용을 위에 요약."""
    labels = []
    if ans.get("install"):
        labels.append(ans["install"])
    hh = dict(E.HOUSEHOLD_OPTS).get(ans.get("household"))
    if hh:
        labels.append(hh)
    ck = dict(E.COOKING_OPTS).get(ans.get("cooking"))
    if ck:
        labels.append(ck.split(" (")[0])
    if ans.get("door_style"):
        labels.append({"양문형": "양문형", "4도어_no_ai": "4도어",
                       "4도어_ai": "4도어 AI"}[ans["door_style"]])
    if labels:
        st.markdown('<div class="crumbs">선택: ' + "  ·  ".join(labels) + "</div>",
                    unsafe_allow_html=True)


def manager(msg):
    st.markdown(f'<div class="manager-bubble">{msg}</div>', unsafe_allow_html=True)


def ask_buttons(opts, key):
    """opts: list of (value, label[, sublabel]). 클릭 시 ans[key]=value."""
    for opt in opts:
        val, label = opt[0], opt[1]
        sub = opt[2] if len(opt) > 2 else None
        btn_label = f"{label}\n\n{sub}" if sub else label
        if st.button(btn_label, key=f"{key}_{val}", use_container_width=True):
            ans[key] = val
            st.rerun()


# ── 헤더 ──
st.title("LG 냉장고 상담")
st.caption("베스트샵 매니저처럼, 몇 가지만 여쭤보고 딱 맞는 냉장고를 찾아드려요.")
crumbs()

q = E.next_question(PRODUCTS, ans)

# ── 질문 단계 ──
if q == "install":
    manager("안녕하세요! 냉장고를 <b>어떻게 설치</b>하실 계획이세요?")
    ask_buttons(E.INSTALL_OPTS, "install")

elif q == "household":
    manager("네, 좋아요. <b>몇 분이</b> 함께 쓰실 냉장고일까요?")
    ask_buttons(E.HOUSEHOLD_OPTS, "household")

elif q == "cooking":
    manager("<b>요리는 얼마나 자주</b> 하시는 편이에요? 보관할 식재료 양을 가늠하려고요.")
    ask_buttons(E.COOKING_OPTS, "cooking")

elif q == "door_style":
    manager("대용량으로 보시는군요! <b>문 여는 방식</b>은 어떤 게 편하세요?")
    ask_buttons([
        ("양문형", "양문형", "좌우로 활짝 — 폭이 넉넉해요"),
        ("4도어_no_ai", "4도어", "위·아래 분리 — 합리적인 선택"),
        ("4도어_ai", "4도어 + AI", "자동 절전·신선 케어까지"),
    ], "door_style")

elif q == "space":
    manager("설치하실 <b>자리 폭</b>은 어느 정도예요?")
    ask_buttons([
        ("slim", "좁은 편이에요", "슬림하게 들어가야 해요 (폭 60cm 이하)"),
        ("normal", "일반적이에요", "보통 주방 공간"),
        ("roomy", "넉넉해요", "공간 여유가 있어요"),
    ], "space")

elif q == "features":
    cand, _ = E.filter_candidates(PRODUCTS, ans)
    feats = E.available_soft_features(cand)
    manager("거의 다 왔어요! <b>특별히 원하시는 기능</b>이 있으면 골라주세요. "
            "(없으면 그냥 넘어가셔도 돼요)")
    chosen = []
    for key, label in feats:
        if st.checkbox(label, key=f"feat_{key}"):
            chosen.append(key)
    if st.button("이걸로 추천받기", type="primary", use_container_width=True):
        ans["wanted_features"] = chosen
        st.rerun()

# ── 결과 ──
elif q == "result":
    cand, tier = E.filter_candidates(PRODUCTS, ans)
    if "wanted_features" not in ans:
        ans["wanted_features"] = []
    ranked = E.score_and_rank(cand, ans)

    if not ranked:
        manager("조건에 딱 맞는 제품을 못 찾았어요. 처음부터 다시 해볼까요?")
    else:
        top_score, top, top_hit = ranked[0]
        manager(f"고객님께는 <b>이 냉장고</b>를 추천드려요!")

        def card(p, hit, is_top, score):
            cls = "rec-card top" if is_top else "rec-card"
            price = (f"{p['price_min']:,}원" if p["price_min"] == p["price_max"]
                     else f"{p['price_min']:,}~{p['price_max']:,}원")
            chips = "".join(f'<span class="chip">{SOFT_FEATURES[k][0].split(" (")[0]}</span>'
                            for k in sorted(p["features"]))
            color = ", ".join(p["colors"][:4]) if p["colors"] else "-"
            html = f'''<div class="{cls}">
              <div style="font-size:1.15rem;font-weight:700;">{p["name"]}</div>
              <div class="spec">{p["code"]} · {p["install"]} · {p["doors"]} · 총 {p["total_l"]}L · 에너지 {p["energy"]}등급</div>
              <div class="price" style="margin:8px 0;">{price}</div>
              <div>{chips}</div>
              <div class="spec" style="margin-top:6px;">색상: {color} &nbsp;|&nbsp; 크기(WxHxD): {p["size_raw"]}</div>
            </div>'''
            st.markdown(html, unsafe_allow_html=True)

        card(top, top_hit, True, top_score)
        st.markdown("**이 제품을 추천드리는 이유**")
        for r in E.reasons_for(top, ans, tier):
            st.markdown(f"- {r}")

        alts = ranked[1:3]
        if alts:
            st.markdown("---")
            st.markdown("**함께 비교해 보면 좋은 제품**")
            for sc, p, hit in alts:
                card(p, hit, False, sc)

    st.markdown("---")
    if st.button("처음부터 다시 상담", use_container_width=True):
        reset()
        st.rerun()

# ── 뒤로/리셋 (질문 중에만) ──
if q != "result" and ans:
    st.markdown("")
    if st.button("← 처음부터", key="restart_top"):
        reset()
        st.rerun()
