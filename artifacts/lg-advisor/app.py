"""LG 가전 상담 — 범용 프리미엄 UI.
카테고리·질문·선택지는 모두 ui_config.py에서 주입받습니다.
"""
import json
import streamlit as st
import streamlit.components.v1 as components
from data_loader import load_products, SOFT_FEATURES
import engine as E
from ui_config import REFRIGERATOR_CONFIG, ICONS

# ── 설정 선택 (향후 다른 카테고리 추가 시 이 줄만 변경) ──
CFG = REFRIGERATOR_CONFIG

st.set_page_config(
    page_title=f"LG {CFG.name} 상담",
    page_icon="LG",
    layout="centered",
)

PRODUCTS, IS_SAMPLE = load_products()

if "answers" not in st.session_state:
    st.session_state.answers = {}
if "history" not in st.session_state:
    st.session_state.history = []   # 답변한 q_id 순서 목록

ans = st.session_state.answers


def reset():
    st.session_state.answers = {}
    st.session_state.history = []


def go_back():
    """가장 최근 답변 하나를 취소하고 직전 질문으로 돌아간다."""
    h = st.session_state.history
    if h:
        last_q = h.pop()
        st.session_state.answers.pop(last_q, None)


def jump_to(q_id: str):
    """해당 질문 단계로 점프 — 그 단계 이후 답변은 모두 초기화."""
    h = st.session_state.history
    if q_id in h:
        idx = h.index(q_id)
        removed = h[idx:]
        st.session_state.history = h[:idx]
        for k in removed:
            st.session_state.answers.pop(k, None)


# ── 라벨 → 아이콘/설명 매핑 (JS에 주입) ───────────────────────────────
label_icon: dict[str, str] = {}
label_desc: dict[str, str] = {}
for qc in CFG.questions.values():
    for opt in qc.options:
        label_icon[opt.label] = opt.icon_key
        label_desc[opt.label] = opt.desc

label_icon_json = json.dumps(label_icon, ensure_ascii=False)
label_desc_json = json.dumps(label_desc, ensure_ascii=False)
icons_json = json.dumps(ICONS, ensure_ascii=False)


# ── 글로벌 CSS ────────────────────────────────────────────────────────
GLOBAL_CSS = f"""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');

*, *::before, *::after {{
  font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  box-sizing: border-box;
}}

/* ── 배경 / 레이아웃 ── */
.stApp, [data-testid="stAppViewContainer"] > .main {{
  background: #FFFFFF !important;
}}
[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stDecoration"] {{ display: none !important; }}
.block-container {{
  max-width: 640px !important;
  padding: 2.8rem 1.5rem 5rem !important;
  margin: 0 auto !important;
}}

/* ── 헤더 ── */
.lg-header {{
  margin-bottom: 2.4rem;
}}
.lg-wordmark {{
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  color: #A50034;
  text-transform: uppercase;
  margin-bottom: 0.45rem;
}}
.lg-title {{
  font-size: 1.9rem;
  font-weight: 800;
  color: #111111;
  letter-spacing: -0.025em;
  line-height: 1.15;
  margin-bottom: 0.45rem;
}}
.lg-subtitle {{
  font-size: 0.88rem;
  color: #888888;
  line-height: 1.45;
  font-weight: 400;
}}

/* ── 진행 뱃지 ── */
.lg-crumbs {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 1.8rem;
}}
.lg-crumb {{
  background: #F5F5F7;
  color: #444;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 4px 11px;
  border-radius: 100px;
  letter-spacing: 0.01em;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}}
.lg-crumb:hover {{
  background: #FFEAEF;
  color: #A50034;
}}

/* ── 질문 말풍선 ── */
.q-bubble {{
  background: #F5F5F7;
  border-radius: 16px;
  padding: 17px 22px;
  margin-bottom: 1.4rem;
  font-size: 0.97rem;
  color: #1A1A1A;
  line-height: 1.65;
  font-weight: 400;
}}
.q-bubble strong {{ color: #111; font-weight: 700; }}
.q-bubble .accent {{ color: #A50034; font-weight: 700; }}

/* ── 선택지 카드 버튼 (secondary) ── */
button[data-testid="stBaseButton-secondary"] {{
  background: #FFFFFF !important;
  border: 1.5px solid #E8E8E8 !important;
  border-radius: 14px !important;
  padding: 16px 20px !important;
  box-shadow: 0 2px 10px rgba(0,0,0,0.045) !important;
  width: 100% !important;
  justify-content: flex-start !important;
  align-items: center !important;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease !important;
  animation: lgFadeUp 0.22s ease both;
}}
button[data-testid="stBaseButton-secondary"]:hover {{
  border-color: #A50034 !important;
  box-shadow: 0 8px 24px rgba(165,0,52,0.09) !important;
  transform: translateY(-2px) !important;
  background: #FFFFFF !important;
}}
/* 버튼 내부 컨테이너 */
button[data-testid="stBaseButton-secondary"] > div {{
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
}}
/* 텍스트 단락 */
button[data-testid="stBaseButton-secondary"] p {{
  width: 100% !important;
  text-align: left !important;
  margin: 0 !important;
  font-size: 0.93rem !important;
  font-weight: 600 !important;
  color: #1A1A1A !important;
}}

/* 카드 간격 */
div[data-testid="stButton"] {{
  margin-bottom: 8px !important;
}}

/* ── 뒤로가기 버튼 오버라이드 (JS가 .lg-back-btn 클래스 추가) ── */
button.lg-back-btn {{
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: #AAA !important;
  font-size: 0.82rem !important;
  font-weight: 500 !important;
  padding: 4px 0 !important;
  transform: none !important;
  animation: none !important;
}}
button.lg-back-btn:hover {{
  color: #555 !important;
  border: none !important;
  box-shadow: none !important;
  transform: none !important;
}}

/* ── 기본(Primary) 버튼 ── */
button[data-testid="stBaseButton-primary"] {{
  background: #A50034 !important;
  border: none !important;
  border-radius: 10px !important;
  color: #fff !important;
  font-weight: 700 !important;
  font-size: 0.93rem !important;
  padding: 14px !important;
  letter-spacing: 0.01em !important;
  transition: background 0.18s, transform 0.18s, box-shadow 0.18s !important;
  animation: none !important;
}}
button[data-testid="stBaseButton-primary"]:hover {{
  background: #8A0029 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 18px rgba(165,0,52,0.22) !important;
}}

/* ── 체크박스 ── */
div[data-testid="stCheckbox"] {{
  border: 1.5px solid #E8E8E8;
  border-radius: 12px;
  padding: 13px 18px;
  margin-bottom: 8px;
  background: #fff;
  transition: border-color 0.18s;
  animation: lgFadeUp 0.22s ease both;
}}
div[data-testid="stCheckbox"]:hover {{ border-color: #A50034; }}
div[data-testid="stCheckbox"] label {{
  font-size: 0.88rem !important;
  font-weight: 500 !important;
  color: #1A1A1A !important;
}}
div[data-testid="stCheckbox"] label span {{
  color: #1A1A1A !important;
}}

/* ── 구분선 ── */
[data-testid="stHorizontalRule"] hr {{
  border-color: #F0F0F0 !important;
  margin: 1.8rem 0 !important;
}}

/* ── 결과 카드 ── */
.res-card {{
  border: 1.5px solid #E8E8E8;
  border-radius: 16px;
  padding: 22px 24px;
  background: #fff;
  margin-bottom: 12px;
  animation: lgFadeUp 0.25s ease both;
}}
.res-card.top-pick {{
  border: 2.5px solid #A50034 !important;
  background: #FFF8FA;
  box-shadow: 0 4px 20px rgba(165,0,52,0.10);
}}

/* ── 적합도 헤더 줄 ── */
.res-fit-row {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}}
.res-rank {{
  font-size: 0.72rem;
  font-weight: 800;
  color: #BBB;
  letter-spacing: 0.06em;
}}
.res-rank.top {{
  color: #A50034;
}}
/* 적합도 숫자 + 바 */
.res-fit-block {{
  text-align: right;
}}
.res-fit-pct {{
  font-size: 2rem;
  font-weight: 900;
  line-height: 1;
  letter-spacing: -0.04em;
  color: #111;
}}
.res-fit-pct.top {{ color: #A50034; }}
.res-fit-label {{
  font-size: 0.68rem;
  color: #AAA;
  font-weight: 500;
  margin-top: 2px;
}}
.res-fit-bar-wrap {{
  height: 4px;
  background: #F0F0F0;
  border-radius: 2px;
  margin-top: 6px;
  overflow: hidden;
}}
.res-fit-bar {{
  height: 4px;
  border-radius: 2px;
  background: #E8E8E8;
  transition: width 0.6s ease;
}}
.res-fit-bar.top {{ background: #A50034; }}

/* 적합도 배지 */
.res-fit-badge {{
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 100px;
  margin-bottom: 8px;
  letter-spacing: 0.02em;
}}
.res-fit-badge.great {{
  background: #FFF0F3;
  color: #A50034;
  border: 1px solid #FFCCD6;
}}
.res-fit-badge.good {{
  background: #F5F5F7;
  color: #555;
  border: 1px solid #E0E0E0;
}}

.res-name {{
  font-size: 1.05rem;
  font-weight: 700;
  color: #111;
  line-height: 1.3;
  margin-bottom: 4px;
}}
.res-spec {{
  font-size: 0.78rem;
  color: #888;
  margin-bottom: 10px;
  line-height: 1.5;
}}
.res-price {{
  font-size: 1.25rem;
  font-weight: 800;
  color: #A50034;
  margin-bottom: 10px;
  letter-spacing: -0.02em;
}}
.res-chips {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}}
.res-chip {{
  background: #F5F5F7;
  border-radius: 100px;
  padding: 3px 11px;
  font-size: 0.74rem;
  font-weight: 500;
  color: #444;
}}
.res-color {{
  font-size: 0.78rem;
  color: #aaa;
}}

/* ── 애니메이션 ── */
@keyframes lgFadeUp {{
  from {{ opacity: 0; transform: translateY(10px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}
</style>
"""

# ── JS 아이콘 주입 (MutationObserver + polling) ─────────────────────────
ICON_JS = f"""
<script>
(function() {{
  const LABEL_ICONS = {label_icon_json};
  const LABEL_DESCS = {label_desc_json};
  const SVG_ICONS   = {icons_json};

  function makeSvg(key) {{
    const d = SVG_ICONS[key] || SVG_ICONS['default'];
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"'
      + ' stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"'
      + ' style="width:19px;height:19px;flex-shrink:0;">' + d + '</svg>';
  }}

  let _paused = false;

  /* components.html()은 iframe에서 실행 → 부모 프레임 document에 스타일 주입 */
  const parentDoc = window.parent.document;

  function injectHeadStyles() {{
    if (parentDoc.getElementById('lg-runtime-styles')) return;
    const s = parentDoc.createElement('style');
    s.id = 'lg-runtime-styles';
    s.textContent = [
      'button[data-testid="stBaseButton-secondary"] {{',
      '  background:#FFFFFF!important;',
      '  border:1.5px solid #E8E8E8!important;',
      '  border-radius:14px!important;',
      '  box-shadow:0 2px 10px rgba(0,0,0,.045)!important;',
      '  justify-content:flex-start!important;',
      '  padding:16px 20px!important;',
      '  transition:border-color .18s,box-shadow .18s,transform .18s!important;',
      '}}',
      'button[data-testid="stBaseButton-secondary"]:hover {{',
      '  border-color:#A50034!important;',
      '  box-shadow:0 8px 24px rgba(165,0,52,.09)!important;',
      '  transform:translateY(-2px)!important;',
      '  background:#FFFFFF!important;',
      '}}',
      'button[data-testid="stBaseButton-secondary"]>div {{',
      '  width:100%!important;display:flex!important;align-items:center!important;',
      '}}',
      'button[data-testid="stBaseButton-secondary"] p {{',
      '  text-align:left!important;width:100%!important;margin:0!important;',
      '}}',
      'button[data-testid="stBaseButton-primary"] {{',
      '  background:#A50034!important;border:none!important;',
      '  border-radius:10px!important;color:#fff!important;',
      '  font-weight:700!important;letter-spacing:.01em!important;',
      '}}',
      'button[data-testid="stBaseButton-primary"]:hover {{',
      '  background:#8A0029!important;transform:translateY(-1px)!important;',
      '  box-shadow:0 6px 18px rgba(165,0,52,.22)!important;',
      '}}',
      'button.lg-back-btn {{',
      '  background:transparent!important;border:none!important;',
      '  box-shadow:none!important;color:#AAA!important;',
      '  font-size:.82rem!important;transform:none!important;',
      '}}',
      'button.lg-back-btn:hover{{color:#555!important;}}',
    ].join('\\n');
    parentDoc.head.appendChild(s);
  }}

  function enhance() {{
    if (_paused) return;
    injectHeadStyles();
    parentDoc.querySelectorAll('button[data-testid="stBaseButton-secondary"]')
      .forEach(btn => {{

        const rawText = (btn.textContent || '').trim();

        /* 뒤로가기/이전/처음부터 텍스트 링크 스타일 */
        if (rawText.startsWith('←') || rawText.startsWith('↩')) {{
          btn.classList.add('lg-back-btn');
          return;
        }}

        /* 이미 처리된 카드 건너뜀 */
        if (btn.dataset.lgDone === '1') return;

        const p = btn.querySelector('p');
        if (!p) return;

        const title = (p.textContent || '').trim();
        if (!title) return;
        const desc  = LABEL_DESCS[title] || '';
        const iKey  = LABEL_ICONS[title] || 'default';

        /* 인라인 스타일 직접 설정 (Emotion CSS를 확실히 오버라이드) */
        btn.style.justifyContent = 'flex-start';
        btn.style.padding = '16px 20px';

        /* MutationObserver 일시 중지 → DOM 수정 → 재개 */
        _paused = true;
        p.style.cssText = 'display:flex!important;align-items:center!important;'
          + 'width:100%!important;margin:0!important;gap:14px!important;';
        p.innerHTML =
          '<span style="display:flex;align-items:center;justify-content:center;'
          + 'width:40px;height:40px;min-width:40px;border-radius:10px;'
          + 'background:#F5F5F7;color:#555555;flex-shrink:0;" class="lg-icon-box">'
          + makeSvg(iKey) + '</span>'
          + '<span style="flex:1;min-width:0;text-align:left;">'
          + '<span style="display:block;font-size:0.93rem;font-weight:700;'
          + 'color:#111;line-height:1.3;">' + title + '</span>'
          + (desc
              ? '<span style="display:block;font-size:0.78rem;font-weight:400;'
                + 'color:#999;margin-top:3px;line-height:1.3;">' + desc + '</span>'
              : '')
          + '</span>'
          + '<span style="color:#D0D0D0;font-size:1.1rem;flex-shrink:0;">›</span>';
        btn.dataset.lgDone = '1';
        _paused = false;
      }});

  }}

  /* 페이지 로드 후 즉시 + 짧은 간격 반복 실행 (React 렌더 완료 후 확실히 반영) */
  [0, 80, 200, 500, 1000].forEach(ms => setTimeout(enhance, ms));

  /* Streamlit 재실행 시에도 대응 (부모 프레임 body 감지) */
  const mo = new MutationObserver(() => {{ if (!_paused) enhance(); }});
  mo.observe(parentDoc.body, {{ childList: true, subtree: true }});
}})();
</script>
"""


# ── 헬퍼 함수 ────────────────────────────────────────────────────────

def render_header():
    crumb_data: list[tuple[str, str]] = []   # (q_id, display_label)
    if ans.get("install"):
        crumb_data.append(("install", ans["install"]))
    hh = dict(E.HOUSEHOLD_OPTS).get(ans.get("household"))
    if hh:
        crumb_data.append(("household", hh.split(" (")[0]))
    ck = dict(E.COOKING_OPTS).get(ans.get("cooking"))
    if ck:
        crumb_data.append(("cooking", ck.split(" (")[0]))
    if ans.get("door_style"):
        ds_map = {"양문형": "양문형", "4도어_no_ai": "4도어", "4도어_ai": "4도어 AI"}
        crumb_data.append(("door_style", ds_map.get(ans["door_style"], "")))

    crumbs_html = ""
    if crumb_data:
        crumbs_html = '<div class="lg-crumbs">' + "".join(
            f'<span class="lg-crumb" data-qid="{qid}">{lbl}</span>'
            for qid, lbl in crumb_data
        ) + '</div>'

    st.markdown(f"""
    <div class="lg-header">
      <div class="lg-wordmark">LG Electronics</div>
      <div class="lg-title">LG {CFG.name} 상담</div>
      <div class="lg-subtitle">{CFG.subtitle}</div>
    </div>
    {crumbs_html}
    """, unsafe_allow_html=True)


def q_bubble(text: str):
    st.markdown(f'<div class="q-bubble">{text}</div>', unsafe_allow_html=True)


def option_buttons(q_id: str):
    """ui_config 기반 선택지 카드 렌더링.
    라벨만 버튼에 표시하고, JS가 아이콘·설명을 후처리합니다."""
    q_cfg = CFG.questions.get(q_id)
    if not q_cfg:
        return
    q_bubble(q_cfg.text)
    for opt in q_cfg.options:
        if st.button(opt.label, key=f"opt_{q_id}_{opt.value}", use_container_width=True):
            h = st.session_state.history
            if q_id in h:
                # 이미 답변한 질문을 다시 선택 → 이후 답변 모두 초기화
                idx = h.index(q_id)
                for k in h[idx + 1:]:
                    st.session_state.answers.pop(k, None)
                st.session_state.history = h[:idx + 1]
            else:
                h.append(q_id)
            ans[q_id] = opt.value
            st.rerun()


def compute_fit_score(p: dict, ans: dict, applied_tier) -> float:
    """UI 표시용 종합 적합도 (0.0~1.0). 후보 필터링 로직은 engine.py 그대로."""
    parts: list[tuple[float, float]] = []   # (score, weight)

    # ① 용량 적합도 (40%) — 목표 tier와의 거리
    if applied_tier and p.get("total_l"):
        actual = E.tier_index(p["total_l"]) or applied_tier
        diff = abs(actual - applied_tier)
        vol = max(0.0, 1.0 - diff * 0.22)
        parts.append((vol, 0.40))

    # ② 원하는 기능 매칭 (35%)
    wanted = set(ans.get("wanted_features", []))
    if wanted:
        hit = wanted & p.get("features", set())
        parts.append((len(hit) / len(wanted), 0.35))

    # ③ 에너지 등급 (15%): 1등급→1.0, 2→0.85, 3→0.70, …
    energy = p.get("energy")
    if energy:
        parts.append((max(0.0, 1.0 - (energy - 1) * 0.15), 0.15))

    # ④ 기본 매칭 보정 — 나머지 가중치는 항상 100%
    used_w = sum(w for _, w in parts)
    remaining = round(1.0 - used_w, 6)
    if remaining > 0.001:
        parts.append((1.0, remaining))

    total_w = sum(w for _, w in parts)
    if total_w == 0:
        return 0.82
    return sum(s * w for s, w in parts) / total_w


def show_result_card(p: dict, rank: int, fit: float, ans: dict, applied_tier):
    """rank: 1-based 순위, fit: 0.0~1.0 적합도."""
    is_top = (rank == 1)
    card_cls = "res-card top-pick" if is_top else "res-card"
    rank_cls = "res-rank top" if is_top else "res-rank"
    pct = round(fit * 100)
    pct_cls = "res-fit-pct top" if is_top else "res-fit-pct"
    bar_cls = "res-fit-bar top" if is_top else "res-fit-bar"

    # 적합도 배지
    if pct >= 90:
        badge_html = '<span class="res-fit-badge great">매우 잘 맞아요</span>'
    elif pct >= 75:
        badge_html = '<span class="res-fit-badge good">잘 맞아요</span>'
    else:
        badge_html = ""

    price_str = (
        f"{p['price_min']:,}원" if p["price_min"] == p["price_max"]
        else f"{p['price_min']:,} ~ {p['price_max']:,}원"
    ) if p.get("price_min") else "가격 미정"
    color_str = ", ".join(p["colors"][:4]) if p.get("colors") else "—"
    chips_html = "".join(
        f'<span class="res-chip">{SOFT_FEATURES[k][0].split(" (")[0]}</span>'
        for k in sorted(p.get("features", []))
    )

    st.markdown(f"""
    <div class="{card_cls}">
      <div class="res-fit-row">
        <div>
          <div class="{rank_cls}">#{rank} 추천</div>
          {badge_html}
        </div>
        <div class="res-fit-block">
          <div class="{pct_cls}">{pct}<span style="font-size:1rem;font-weight:700;">%</span></div>
          <div class="res-fit-label">종합 적합도</div>
          <div class="res-fit-bar-wrap">
            <div class="{bar_cls}" style="width:{pct}%;"></div>
          </div>
        </div>
      </div>
      <div class="res-name">{p['name']}</div>
      <div class="res-spec">{p['code']} &nbsp;·&nbsp; {p['install']} &nbsp;·&nbsp;
        {p['doors']} &nbsp;·&nbsp; 총 {p['total_l']}L &nbsp;·&nbsp; 에너지 {p['energy']}등급</div>
      <div class="res-price">{price_str}</div>
      <div class="res-chips">{chips_html}</div>
      <div class="res-color">색상: {color_str}&nbsp;&nbsp;|&nbsp;&nbsp;크기(WxHxD): {p['size_raw']}</div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
# 앱 렌더링
# ════════════════════════════════════════════════════════════════════
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

render_header()

if IS_SAMPLE:
    st.markdown("""
    <div style="background:#FFFBF0;border:1.5px solid #FFE082;border-radius:12px;
                padding:13px 18px;font-size:0.82rem;color:#7A5C00;margin-bottom:1.4rem;
                line-height:1.6;">
      <strong>시연 모드</strong> — 샘플 데이터 13개로 동작 중이에요.<br>
      <code>LG_냉장고_대표상품기준_통합DB.xlsx</code>를
      <code>artifacts/lg-advisor/</code> 폴더에 업로드하면 실제 데이터로 전환됩니다.
    </div>
    """, unsafe_allow_html=True)

q = E.next_question(PRODUCTS, ans)

# ── 질문 흐름 ──
if q == "install":
    option_buttons("install")

elif q == "household":
    option_buttons("household")

elif q == "cooking":
    option_buttons("cooking")

elif q == "door_style":
    option_buttons("door_style")

elif q == "space":
    option_buttons("space")

elif q == "features":
    cand, _ = E.filter_candidates(PRODUCTS, ans)
    feats = E.available_soft_features(cand)
    q_bubble("거의 다 왔어요! <strong>원하시는 기능</strong>을 골라주세요. (없으면 그냥 넘어가도 됩니다)")
    chosen = []
    for key, label in feats:
        if st.checkbox(label, key=f"feat_{key}"):
            chosen.append(key)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("이 기능으로 추천받기", type="primary", use_container_width=True):
        h = st.session_state.history
        if "features" not in h:
            h.append("features")
        ans["wanted_features"] = chosen
        st.rerun()

# ── 결과 ──
elif q == "result":
    cand, tier = E.filter_candidates(PRODUCTS, ans)
    if "wanted_features" not in ans:
        ans["wanted_features"] = []
    ranked = E.score_and_rank(cand, ans)   # engine.py 로직 그대로

    if not ranked:
        st.markdown("""
        <div class="q-bubble" style="color:#888;">
          조건에 딱 맞는 제품을 찾지 못했어요. 처음부터 다시 시도해 보세요.
        </div>""", unsafe_allow_html=True)
    else:
        # Top 5만 표시
        top5 = ranked[:5]

        # 적합도 계산 (UI 표시 전용 — 필터링/랭킹 로직 불변)
        scored = [
            (compute_fit_score(p, ans, tier), rank_i + 1, p)
            for rank_i, (_, p, _) in enumerate(top5)
        ]

        # 결과 헤더
        st.markdown(f"""
        <div style="margin-bottom:1.4rem;">
          <div style="font-size:0.72rem;font-weight:800;letter-spacing:0.12em;
                      color:#A50034;text-transform:uppercase;margin-bottom:6px;">
            맞춤 추천 결과
          </div>
          <div style="font-size:1.15rem;font-weight:700;color:#111;line-height:1.3;">
            {len(scored)}개 제품을 찾았어요
          </div>
        </div>
        """, unsafe_allow_html=True)

        # 1위 카드 + 추천 이유
        fit1, _, top_p = scored[0]
        show_result_card(top_p, rank=1, fit=fit1, ans=ans, applied_tier=tier)

        reasons = E.reasons_for(top_p, ans, tier)
        if reasons:
            reason_items = "".join(
                f'<li style="margin-bottom:5px;">{r}</li>' for r in reasons
            )
            st.markdown(f"""
            <div style="margin:-4px 0 16px;padding:14px 20px;background:#F9F9FB;
                        border-radius:0 0 12px 12px;border:1px solid #F0F0F0;border-top:none;">
              <div style="font-size:0.74rem;font-weight:700;color:#777;
                          letter-spacing:0.06em;text-transform:uppercase;margin-bottom:8px;">
                추천 이유
              </div>
              <ul style="margin:0;padding-left:18px;font-size:0.83rem;color:#555;line-height:1.65;">
                {reason_items}
              </ul>
            </div>
            """, unsafe_allow_html=True)

        # 2~5위 카드
        if len(scored) > 1:
            st.markdown("""
            <div style="font-size:0.74rem;font-weight:700;color:#999;
                        letter-spacing:0.06em;text-transform:uppercase;
                        margin:20px 0 10px;">
              다른 후보도 살펴보세요
            </div>
            """, unsafe_allow_html=True)
            for fit_s, rank_s, p_s in scored[1:]:
                show_result_card(p_s, rank=rank_s, fit=fit_s, ans=ans, applied_tier=tier)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if st.button("처음부터 다시 상담", type="primary", use_container_width=True):
        reset()
        st.rerun()

# ── 하단 네비게이션 (이전 / 처음부터) ──
if q != "result" and ans:
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    col_prev, col_reset = st.columns(2)
    with col_prev:
        if st.button("← 이전", key="go_back", use_container_width=True):
            go_back()
            st.rerun()
    with col_reset:
        if st.button("← 처음부터", key="restart_top", use_container_width=True):
            reset()
            st.rerun()

# ── 아이콘 JS 주입 (components.html → iframe → window.parent.document 접근) ──
# height=0 으로 invisible iframe, 실제 DOM 조작은 부모 프레임에서 수행
components.html(ICON_JS, height=0)
