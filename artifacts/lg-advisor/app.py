"""LG 가전 상담 — 범용 프리미엄 UI.
카테고리·질문·선택지는 모두 ui_config.py에서 주입받습니다.
"""
import json
import os
import streamlit as st
import streamlit.components.v1 as components
from data_loader import load_products, SOFT_FEATURES
import engine as E
from ui_config import REFRIGERATOR_CONFIG, ICONS

# ── SKU 데이터 (색상 변형 연동용) ──
_SKU_PATH = os.path.join(os.path.dirname(__file__), "lg_products_sku.json")
try:
    with open(_SKU_PATH, encoding="utf-8") as _f:
        _SKU_INDEX = {p["rep_code"]: p for p in json.load(_f)}
except Exception:
    _SKU_INDEX = {}

# 색상명 → 배경색 hex 매핑 (시각적 스와치용)
_COLOR_HEX: dict[str, str] = {
    "화이트":        "#F5F5F5",
    "슈퍼 화이트":   "#FAFAFA",
    "크림 화이트":   "#FDF8EF",
    "퓨어":          "#E8E8E8",
    "샤인":          "#D4C8B0",
    "다크 그라파이트": "#3C3C3C",
    "그라파이트":    "#5A5A5A",
    "베이지":        "#D4B896",
    "크림":          "#EFE8D8",
    "네이처 그린":   "#7C9E7E",
    "오브제 블루":   "#8DA5BD",
    "오브제 그린":   "#8FA67E",
    "오브제 핑크":   "#D4A5A0",
    "오브제 크림":   "#EFE8D8",
    "블랙":          "#1C1C1C",
    "미스트 블루":   "#A8BFD4",
    "미스트 그린":   "#A8C4A4",
    "미스트 베이지": "#D8C8B4",
}

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
    st.session_state.history = []
if "force_result" not in st.session_state:
    st.session_state.force_result = False

ans = st.session_state.answers


def reset():
    st.session_state.answers = {}
    st.session_state.history = []
    st.session_state.force_result = False


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

/* ── 조건별 적합도 섹션 ── */
.bd-section {{
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid #F0F0F0;
}}
.bd-section-title {{
  font-size: 0.7rem;
  font-weight: 700;
  color: #AAA;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 10px;
}}
.bd-row {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 7px;
}}
.bd-label {{
  font-size: 0.75rem;
  font-weight: 600;
  color: #555;
  width: 38px;
  flex-shrink: 0;
}}
.bd-track {{
  flex: 1;
  height: 6px;
  background: #F0F0F0;
  border-radius: 3px;
  overflow: hidden;
}}
.bd-fill {{
  height: 6px;
  border-radius: 3px;
  background: #22C55E;
  transition: width 0.5s ease;
}}
.bd-fill.mid {{ background: #F59E0B; }}
.bd-fill.low {{ background: #EF4444; }}
.bd-pct {{
  font-size: 0.72rem;
  font-weight: 700;
  color: #777;
  width: 34px;
  text-align: right;
  flex-shrink: 0;
}}
/* 잘 맞는 조건 불릿 */
.bd-bullets {{
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid #F0F0F0;
}}
.bd-bullets-title {{
  font-size: 0.7rem;
  font-weight: 700;
  color: #AAA;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 7px;
}}
.bd-bullet-item {{
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 0.78rem;
  color: #444;
  line-height: 1.5;
  margin-bottom: 3px;
}}
.bd-bullet-dot {{
  width: 6px;
  height: 6px;
  background: #22C55E;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}}

/* ── 통계 박스 ── */
.stat-row {{
  display: flex;
  gap: 10px;
  margin-bottom: 1.4rem;
}}
.stat-box {{
  flex: 1;
  background: #FAFAFA;
  border: 1.5px solid #F0F0F0;
  border-radius: 12px;
  padding: 13px 14px;
  text-align: center;
}}
.stat-num {{
  font-size: 1.55rem;
  font-weight: 800;
  color: #111;
  line-height: 1;
  margin-bottom: 5px;
}}
.stat-num.highlight {{ color: #A50034; }}
.stat-label {{
  font-size: 0.69rem;
  font-weight: 600;
  color: #AAA;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}}

/* ── 비교표 ── */
.cmp-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.79rem;
  color: #333;
}}
.cmp-table th {{
  background: #F5F5F7;
  font-size: 0.68rem;
  font-weight: 700;
  color: #888;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1.5px solid #E8E8E8;
  white-space: nowrap;
}}
.cmp-table td {{
  padding: 9px 10px;
  border-bottom: 1px solid #F0F0F0;
  vertical-align: top;
  line-height: 1.4;
}}
.cmp-table tr:last-child td {{ border-bottom: none; }}
.cmp-table tr.top-row td {{ background: #FFF8F9; }}
.cmp-rank {{ font-weight: 800; color: #A50034; }}
.cmp-name {{ font-weight: 600; color: #111; max-width: 180px; }}
.cmp-fit  {{ font-weight: 700; color: #A50034; white-space: nowrap; }}
.cmp-feat {{ color: #777; font-size: 0.72rem; }}

/* ── 색상 스와치 섹션 ── */
.cs-section {{
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #F0F0F0;
}}
.cs-row-label {{
  font-size: 0.67rem;
  font-weight: 700;
  color: #BBB;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  margin-bottom: 8px;
}}
.cs-chips {{
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-bottom: 10px;
}}
.cs-chip {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px 5px 8px;
  border: 1.5px solid #E8E8E8;
  border-radius: 100px;
  background: #FAFAFA;
  font-size: 0.76rem;
  font-family: 'Pretendard', 'Apple SD Gothic Neo', sans-serif;
  color: #444;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}}
.cs-chip:hover {{ border-color: #A50034; }}
.cs-chip.active {{
  border-color: #A50034;
  background: #FFF5F7;
  color: #A50034;
  font-weight: 600;
  box-shadow: 0 0 0 2px rgba(165,0,52,0.10);
}}
.cs-dot {{
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid rgba(0,0,0,0.12);
  flex-shrink: 0;
}}
.cs-info-row {{
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 0.76rem;
  color: #666;
}}
.cs-info-label {{
  font-size: 0.67rem;
  font-weight: 700;
  color: #BBB;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}}
.cs-info-val {{
  font-weight: 600;
  color: #333;
  transition: color 0.15s;
}}
.cs-info-sep {{ color: #DDD; margin: 0 2px; }}
/* ── 스펙 드롭다운 (폴백용) ── */
.spec-sel-section {{
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #F0F0F0;
  display: flex;
  gap: 10px;
}}
.spec-sel-wrap {{
  flex: 1;
  min-width: 0;
}}
.spec-sel-label {{
  font-size: 0.67rem;
  font-weight: 700;
  color: #BBB;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  margin-bottom: 5px;
}}
.spec-sel {{
  width: 100%;
  padding: 7px 28px 7px 10px;
  border: 1.5px solid #E8E8E8;
  border-radius: 8px;
  font-size: 0.78rem;
  font-family: 'Pretendard', 'Apple SD Gothic Neo', sans-serif;
  color: #333;
  background: #FAFAFA;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml;charset=utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23AAAAAA' stroke-width='1.5' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 9px center;
  background-size: 10px;
  transition: border-color 0.15s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.spec-sel:hover {{ border-color: #A50034; }}
.spec-sel:focus {{ outline: none; border-color: #A50034; }}

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
      'button.lg-skip-btn{{background:transparent!important;border:1.5px solid #E8E8E8!important;box-shadow:none!important;color:#AAA!important;font-size:.76rem!important;font-weight:500!important;border-radius:8px!important;transform:none!important;padding:6px 18px!important;width:auto!important;}}',
      'button.lg-skip-btn:hover{{color:#A50034!important;border-color:#A50034!important;}}',
      'button.lg-skip-btn p{{text-align:center!important;font-size:.76rem!important;font-weight:500!important;}}',
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
        /* 바로 결과 보기 — 보조 버튼 스타일, 아이콘 처리 제외 */
        if (rawText.includes('바로 결과')) {{
          btn.classList.add('lg-skip-btn');
          btn.style.width = 'auto';
          btn.style.display = 'block';
          btn.style.margin = '0 auto';
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


def show_skip_btn():
    """현재까지 답한 조건만으로 바로 결과 보기 — 보조 버튼."""
    if not ans:   # 아직 아무것도 답하지 않은 첫 화면엔 표시 안 함
        return
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([3, 4, 3])
    with mid:
        if st.button("지금 바로 결과 보기 →", key="skip_to_result", use_container_width=False):
            st.session_state.force_result = True
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


def compute_breakdown(p: dict, ans: dict, applied_tier) -> list[dict]:
    """조건별 점수(0-100) + 불릿 설명 반환. engine.py 로직 불변."""
    rows: list[dict] = []

    # 설치 — 하드 필터 통과한 후보이므로 항상 100
    inst_label = {"빌트인": "빌트인", "Fit & Max": "Fit & Max",
                  "프리스탠딩": "프리스탠딩"}.get(p.get("install", ""), p.get("install", ""))
    rows.append({"label": "설치", "score": 100,
                 "bullet": f"{inst_label} 타입에 딱 맞아요"})

    # 용량 — 목표 tier와의 거리(단계당 25점 감점)
    if applied_tier and p.get("total_l"):
        actual = E.tier_index(p["total_l"]) or applied_tier
        diff = abs(actual - applied_tier)
        score = max(0, 100 - diff * 25)
        tier_name = E.TIER_LABEL.get(applied_tier, "")
        if diff == 0:
            bullet = f"목표 용량({tier_name})에 딱 맞아요"
        elif diff == 1:
            bullet = f"목표 용량({tier_name})과 한 단계 차이나요"
        else:
            bullet = ""
        rows.append({"label": "용량", "score": score,
                     "bullet": bullet if score >= 75 else ""})

    # 예산 — 현재 질문에 없으므로 ans에 budget 키가 있을 때만 표시
    budget = ans.get("budget")
    if budget is not None:
        price = p.get("price_min") or p.get("price_max") or 0
        if price:
            if price <= budget:
                b_score, bullet = 100, "예산 범위 안에 있어요"
            else:
                b_score = max(0, round(budget / price * 100))
                bullet = ""
            rows.append({"label": "예산", "score": b_score,
                         "bullet": bullet if b_score >= 75 else ""})

    # 기능 — 원하는 기능 충족 비율
    wanted = set(ans.get("wanted_features", []))
    if wanted:
        hit = wanted & p.get("features", set())
        f_score = round(len(hit) / len(wanted) * 100)
        if f_score == 100:
            bullet = "원하는 기능을 모두 갖췄어요"
        elif hit:
            labels = [SOFT_FEATURES[k][0].split(" (")[0] for k in list(hit)[:2]]
            bullet = ", ".join(labels) + " 등을 갖췄어요"
        else:
            bullet = ""
        rows.append({"label": "기능", "score": f_score,
                     "bullet": bullet if f_score >= 75 else ""})

    # 에너지 — 1등급 100, 2등급 85, 3등급 70, 4등급 55
    energy = p.get("energy")
    if energy:
        e_map = {1: 100, 2: 85, 3: 70, 4: 55}
        e_score = e_map.get(energy, max(0, 55 - (energy - 4) * 15))
        if energy == 1:
            bullet = "에너지 1등급으로 전기료가 절약돼요"
        elif energy == 2:
            bullet = "에너지 2등급으로 효율이 높아요"
        elif e_score >= 75:
            bullet = f"에너지 {energy}등급이에요"
        else:
            bullet = ""
        rows.append({"label": "에너지", "score": e_score,
                     "bullet": bullet if e_score >= 75 else ""})

    return rows


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

    # 조건별 적합도 계산
    breakdown = compute_breakdown(p, ans, applied_tier)

    # 잘 맞는 조건 불릿 HTML
    good_bullets = [row["bullet"] for row in breakdown if row["bullet"]]
    if good_bullets:
        bullet_items = "".join(
            f'<div class="bd-bullet-item">'
            f'<div class="bd-bullet-dot"></div>'
            f'<span>{b}</span></div>'
            for b in good_bullets
        )
        bullets_html = (
            '<div class="bd-bullets">'
            '<div class="bd-bullets-title">잘 맞는 조건</div>'
            + bullet_items +
            '</div>'
        )
    else:
        bullets_html = ""

    # 조건별 막대 그래프 HTML
    bar_rows_html = ""
    for row in breakdown:
        s = row["score"]
        fill_cls = "bd-fill" if s >= 75 else ("bd-fill mid" if s >= 50 else "bd-fill low")
        bar_rows_html += (
            f'<div class="bd-row">'
            f'<span class="bd-label">{row["label"]}</span>'
            f'<div class="bd-track"><div class="{fill_cls}" style="width:{s}%;"></div></div>'
            f'<span class="bd-pct">{s}%</span>'
            f'</div>'
        )
    bars_html = (
        '<div class="bd-section">'
        '<div class="bd-section-title">조건별 적합도</div>'
        + bar_rows_html +
        '</div>'
    )

    # ── SKU 색상 스와치 섹션 ──────────────────────────────────────────
    rep_code   = p.get("code", "")
    sku        = _SKU_INDEX.get(rep_code)
    variants   = sku["variants"] if sku else []

    # 초기 표시값: variants[0] 또는 제품 기본값
    init_v     = variants[0] if variants else {}
    init_code  = init_v.get("code")  or rep_code
    init_mat   = init_v.get("material") or p.get("material", "")
    init_price = init_v.get("price")
    if init_price:
        disp_price = f"{int(init_price):,}원"
    else:
        disp_price = price_str  # data_loader 계산값 그대로

    ccode_id = f"card-code-{rank}"
    cprc_id  = f"card-price-{rank}"
    cmat_id  = f"card-mat-{rank}"

    if sku and len(variants) > 1:
        # 여러 색상 → 클릭형 스와치
        chip_items = ""
        for idx, v in enumerate(variants):
            cname     = v.get("color", "")
            hex_bg    = _COLOR_HEX.get(cname, "#DDDDDD")
            is_light  = hex_bg.upper() in ("#F5F5F5","#FAFAFA","#FDF8EF","#E8E8E8","#FFFFFF","#FFF")
            dot_border = "rgba(0,0,0,0.18)" if is_light else "rgba(0,0,0,0.08)"
            active_cls = "active" if idx == 0 else ""
            v_code      = v.get("code")     or ""
            v_mat       = v.get("material") or ""
            v_price     = int(v.get("price") or 0)
            v_price_fmt = f"{v_price:,}원" if v_price else ""
            # onclick 대신 data-* 속성 → SWATCH_JS가 이벤트 리스너 부착
            chip_items += (
                f'<button class="cs-chip {active_cls}"'
                f' data-rank="{rank}"'
                f' data-code="{v_code}"'
                f' data-price="{v_price_fmt}"'
                f' data-mat="{v_mat}">'
                f'<span class="cs-dot" style="background:{hex_bg};border:1px solid {dot_border};"></span>'
                f'{cname}</button>'
            )

        mat_display = f'<span class="cs-info-sep">·</span><span class="cs-info-label">재질</span><span class="cs-info-val" id="{cmat_id}">{init_mat}</span>' if init_mat else f'<span id="{cmat_id}"></span>'

        sku_html = (
            '<div class="cs-section">'
            '<div class="cs-row-label">색상</div>'
            f'<div class="cs-chips">{chip_items}</div>'
            '<div class="cs-info-row">'
            '<span class="cs-info-label">모델 코드</span>'
            f'<span class="cs-info-val" id="{ccode_id}">{init_code}</span>'
            f'{mat_display}'
            '</div>'
            '</div>'
        )
    elif sku and len(variants) == 1:
        # 색상 1종 → 스와치 없이 정보만 표시
        single_color = variants[0].get("color", "")
        hex_bg = _COLOR_HEX.get(single_color, "#DDDDDD")
        mat_display = (
            f'<span class="cs-info-sep">·</span>'
            f'<span class="cs-info-label">재질</span>'
            f'<span class="cs-info-val" id="{cmat_id}">{init_mat}</span>'
        ) if init_mat else f'<span id="{cmat_id}"></span>'
        sku_html = (
            '<div class="cs-section">'
            '<div class="cs-chips" style="margin-bottom:10px;">'
            f'<span class="cs-chip active" style="cursor:default;">'
            f'<span class="cs-dot" style="background:{hex_bg};border:1px solid rgba(0,0,0,0.12);"></span>'
            f'{single_color}</span></div>'
            '<div class="cs-info-row">'
            '<span class="cs-info-label">모델 코드</span>'
            f'<span class="cs-info-val" id="{ccode_id}">{init_code}</span>'
            f'{mat_display}'
            '</div>'
            '</div>'
        )
    else:
        # SKU 데이터 없음 → 기존 드롭다운 폴백
        def _opts(vals):
            return "".join(f'<option>{v}</option>' for v in vals)
        colors_sel = p.get("colors") or []
        mats_sel   = p.get("materials") or [p.get("material", "-")]
        codes_sel  = p.get("model_codes") or [p.get("code", "-")]
        color_opts = _opts(colors_sel) if colors_sel else '<option>-</option>'
        mat_opts   = _opts(mats_sel)
        code_opts  = _opts(codes_sel)
        linked     = (len(colors_sel) == len(codes_sel) and len(colors_sel) > 0)
        cid = f"sel-color-{rank}"; kid = f"sel-code-{rank}"; mid_id = f"sel-mat-{rank}"
        if linked:
            co = f"var i=this.selectedIndex;document.getElementById('{kid}').selectedIndex=i;"
            ko = f"var i=this.selectedIndex;document.getElementById('{cid}').selectedIndex=i;"
            color_sel_tag = f'<select class="spec-sel" id="{cid}" onchange="{co}">{color_opts}</select>'
            code_sel_tag  = f'<select class="spec-sel" id="{kid}" onchange="{ko}">{code_opts}</select>'
        else:
            color_sel_tag = f'<select class="spec-sel" id="{cid}">{color_opts}</select>'
            code_sel_tag  = f'<select class="spec-sel" id="{kid}">{code_opts}</select>'
        sku_html = (
            '<div class="spec-sel-section">'
            f'<div class="spec-sel-wrap"><div class="spec-sel-label">색상</div>{color_sel_tag}</div>'
            f'<div class="spec-sel-wrap"><div class="spec-sel-label">도어 재질</div>'
            f'<select class="spec-sel" id="{mid_id}">{mat_opts}</select></div>'
            f'<div class="spec-sel-wrap"><div class="spec-sel-label">모델 코드</div>{code_sel_tag}</div>'
            '</div>'
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
      <div class="res-spec"><span id="{ccode_id}-spec">{init_code}</span> &nbsp;·&nbsp; {p['install']} &nbsp;·&nbsp;
        {p['doors']} &nbsp;·&nbsp; 총 {p['total_l']}L &nbsp;·&nbsp; 에너지 {p['energy']}등급
        &nbsp;·&nbsp; {p['size_raw']}</div>
      <div class="res-price"><span id="{cprc_id}">{disp_price}</span></div>
      <div class="res-chips">{chips_html}</div>
      {sku_html}
      {bullets_html}
      {bars_html}
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

if st.session_state.force_result:
    q = "result"
else:
    q = E.next_question(PRODUCTS, ans)

# ── 질문 흐름 ──
if q == "install":
    option_buttons("install")

elif q == "household":
    option_buttons("household")
    show_skip_btn()

elif q == "cooking":
    option_buttons("cooking")
    show_skip_btn()

elif q == "door_style":
    option_buttons("door_style")
    show_skip_btn()

elif q == "space":
    option_buttons("space")
    show_skip_btn()

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
    show_skip_btn()

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

        # 통계 박스
        q_count = len(st.session_state.get("history", []))
        db_total = len(PRODUCTS)
        cand_count = len(cand)
        st.markdown(f"""
        <div style="margin-bottom:0.5rem;">
          <div style="font-size:0.72rem;font-weight:800;letter-spacing:0.12em;
                      color:#A50034;text-transform:uppercase;margin-bottom:10px;">
            맞춤 추천 결과
          </div>
        </div>
        <div class="stat-row">
          <div class="stat-box">
            <div class="stat-num">{q_count}</div>
            <div class="stat-label">답한 질문</div>
          </div>
          <div class="stat-box">
            <div class="stat-num highlight">{cand_count}</div>
            <div class="stat-label">후보 제품</div>
          </div>
          <div class="stat-box">
            <div class="stat-num">{db_total}</div>
            <div class="stat-label">전체 DB</div>
          </div>
        </div>
        <div style="font-size:1.08rem;font-weight:700;color:#111;margin-bottom:1.2rem;">
          상위 {len(scored)}개 제품을 추천드려요
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

        # Top 5 한눈에 비교표
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        with st.expander("📊 Top 5 한눈에 비교표"):
            # 주요 기능 레이블 매핑
            def _feat_labels(p):
                feats = p.get("features", set())
                labels = [SOFT_FEATURES[k][0].split(" (")[0] for k in sorted(feats)
                          if k in SOFT_FEATURES]
                return ", ".join(labels) if labels else "—"

            rows_html = ""
            for fit_c, rank_c, p_c in scored:
                price_c = (
                    f"{p_c['price_min']:,}원" if p_c.get("price_min") else "미정"
                )
                row_cls = "top-row" if rank_c == 1 else ""
                rows_html += f"""
                <tr class="{row_cls}">
                  <td><span class="cmp-rank">#{rank_c}</span></td>
                  <td><span class="cmp-name">{p_c['name']}</span></td>
                  <td><span class="cmp-fit">{round(fit_c * 100)}%</span></td>
                  <td>{price_c}</td>
                  <td>{p_c.get('total_l', '—')}L</td>
                  <td>{p_c.get('doors', '—')}</td>
                  <td>{p_c.get('energy', '—')}등급</td>
                  <td><span class="cmp-feat">{_feat_labels(p_c)}</span></td>
                </tr>"""

            st.markdown(f"""
            <div style="overflow-x:auto;">
            <table class="cmp-table">
              <thead>
                <tr>
                  <th>순위</th>
                  <th>제품명</th>
                  <th>적합도</th>
                  <th>최저가</th>
                  <th>용량</th>
                  <th>도어</th>
                  <th>에너지</th>
                  <th>주요기능</th>
                </tr>
              </thead>
              <tbody>
                {rows_html}
              </tbody>
            </table>
            </div>
            """, unsafe_allow_html=True)

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

# ── 색상 스와치 JS (components.html → iframe → window.parent.document 접근) ──
# React는 onclick="string" 을 거부하므로, data-* 속성에 값을 담고
# 이 iframe에서 addEventListener로 이벤트를 직접 부착
SWATCH_JS = """
<script>
(function() {
  var doc = window.parent.document;
  /* 부모 document 의 <head> 에 스크립트를 직접 주입 (ICON_JS 의 스타일 주입과 동일 패턴).
     주입된 스크립트는 부모 문서에 영구적으로 살아있어 Streamlit 리렌더 후에도 동작. */
  if (doc.getElementById('lg-swatch-handler')) return;

  var code = [
    '(function(){',
    '  function bind(){',
    '    document.querySelectorAll(".cs-chip[data-rank]:not([data-sw])").forEach(function(c){',
    '      c.setAttribute("data-sw","1");',
    '      c.addEventListener("click",function(){',
    '        var r=c.dataset.rank;',
    '        var ce=document.getElementById("card-code-"+r);',
    '        var pe=document.getElementById("card-price-"+r);',
    '        var me=document.getElementById("card-mat-"+r);',
    '        if(ce) ce.textContent=c.dataset.code||"";',
    '        if(pe) pe.textContent=c.dataset.price||"";',
    '        if(me) me.textContent=c.dataset.mat||"";',
    '        var row=c.closest(".cs-chips");',
    '        if(row) row.querySelectorAll(".cs-chip").forEach(function(x){x.classList.remove("active");});',
    '        c.classList.add("active");',
    '      });',
    '    });',
    '  }',
    '  bind();',
    '  new MutationObserver(bind).observe(document.body,{childList:true,subtree:true});',
    '  setInterval(bind,400);',
    '})();'
  ].join('\\n');

  var s = doc.createElement('script');
  s.id = 'lg-swatch-handler';
  s.textContent = code;
  doc.head.appendChild(s);
})();
</script>
"""

# ── 아이콘 JS 주입 (components.html → iframe → window.parent.document 접근) ──
# height=0 으로 invisible iframe, 실제 DOM 조작은 부모 프레임에서 수행
components.html(ICON_JS, height=0)
components.html(SWATCH_JS, height=0)
