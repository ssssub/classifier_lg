"""LG 가전 상담 — 범용 프리미엄 UI.
카테고리·질문·선택지는 모두 ui_config.py에서 주입받습니다.
"""
import json
import os
import re
import time
import uuid
from html import escape
import streamlit as st
import streamlit.components.v1 as components
from data_loader import load_products, SOFT_FEATURES
import engine as E
import db as DB
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
    "샤이니 유니버스": "#5D5E5B",
    "난방향 스테인": "#87888C",
    "클레이 핑크": "#A18D8C",
    "실버": "#B7B7B7",
    "베이지": "#DAD1CA",
    "토프": "#C4BCB9",
    "에센스 화이트": "#FFFFFF",
    "네이비": "#4C4F5E",
    "오브제 컬렉션": "#C2C2C2",
    "오브제컬렉션": "#F4F6F8",
    "그린": "#2A3C2E",
    "아몬드": "#CCB9B2",
    "클레이 브라운": "#B3A598",
    "크림 스카이": "#E6EAED",
    "크림 그레이": "#A0A0A0",
    "크림 화이트": "#FFFFFF",
    "프라임 실버": "#ADAEB0",
    "핑크": "#CBB0AF",
    "클레이 민트": "#749296",
    "크림 피치": "#E6AC97",
    "크림 라벤더": "#C6BED0",
    "크림 레몬": "#DFD199",
    "맨해튼 미드나잇": "#424448",
    "샤인": "#A1A0A5",
    "몽블랑 네이처": "#ABADB1",
    "네이처 베이지": "#F1FDF7",
    "화이트": "#EDEFF1",
    "퓨어": "#BCBEC0",
    "다크 그라파이트": "#949496",
    "슈퍼 화이트": "#E5E7EB",
    "그라파이트":    "#5A5A5A",
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
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "session_start" not in st.session_state:
    st.session_state.session_start = time.time()
if "_db_logged" not in st.session_state:
    st.session_state._db_logged = False
if "click_count" not in st.session_state:
    st.session_state.click_count = 0
if "_session_start_logged" not in st.session_state:
    st.session_state._session_start_logged = False
if "_rated" not in st.session_state:
    st.session_state._rated = False
if "_survey_submitted" not in st.session_state:
    st.session_state._survey_submitted = False
if "_survey_open" not in st.session_state:
    st.session_state._survey_open = False

ans = st.session_state.answers


def reset():
    st.session_state.answers = {}
    st.session_state.history = []
    st.session_state.force_result = False
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.session_start = time.time()
    st.session_state._db_logged = False
    st.session_state.click_count = 0
    st.session_state._session_start_logged = False
    st.session_state._rated = False
    st.session_state._survey_submitted = False
    st.session_state._survey_open = False


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
  max-width: 940px !important;
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

/* ── 질문 진행률 ── */
.lg-progress-wrap {{
  margin: -0.6rem 0 1.5rem;
}}
.lg-progress-meta {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 7px;
  color: #888;
  font-size: 0.75rem;
  font-weight: 700;
}}
.lg-progress-meta strong {{
  color: #A50034;
  font-weight: 800;
}}
.lg-progress-track {{
  width: 100%;
  height: 7px;
  border-radius: 999px;
  background: #F0F0F0;
  overflow: hidden;
}}
.lg-progress-fill {{
  height: 100%;
  border-radius: inherit;
  background: #A50034;
  transition: width 0.24s ease;
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
.q-bubble .hint {{
  display: inline-block;
  color: #9A9A9A;
  font-size: 0.8rem;
  font-weight: 500;
  line-height: 1.45;
  margin-top: 4px;
}}
.q-bubble .hint-block {{
  display: block;
  color: #9A9A9A;
  font-size: 0.8rem;
  font-weight: 400;
  line-height: 1.5;
  margin-top: 6px;
}}

/* ── 설치공간 입력창 ── */
div[data-testid="stTextInput"] input {{
  border: 1.5px solid #E8E8E8 !important;
  border-radius: 12px !important;
  padding: 12px 16px !important;
  font-size: 0.93rem !important;
  color: #1A1A1A !important;
  background: #FFFFFF !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
  transition: border-color 0.18s !important;
}}
div[data-testid="stTextInput"] input:focus {{
  border-color: #A50034 !important;
  box-shadow: 0 0 0 3px rgba(165,0,52,0.08) !important;
  outline: none !important;
}}
div[data-testid="stTextInput"] input::placeholder {{
  color: #BBBBBB !important;
  font-size: 0.88rem !important;
}}

/* ── 선택지 카드 버튼 (.lg-option-btn) ── */
button[data-testid="stBaseButton-secondary"]:not(.lg-skip-btn):not(.lg-back-btn) {{
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
button[data-testid="stBaseButton-secondary"]:not(.lg-skip-btn):not(.lg-back-btn):hover {{
  border-color: #A50034 !important;
  box-shadow: 0 8px 24px rgba(165,0,52,0.09) !important;
  transform: translateY(-2px) !important;
  background: #FFFFFF !important;
}}
button[data-testid="stBaseButton-secondary"]:not(.lg-skip-btn):not(.lg-back-btn) > div {{
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
}}
button[data-testid="stBaseButton-secondary"]:not(.lg-skip-btn):not(.lg-back-btn) p {{
  width: 100% !important;
  text-align: left !important;
  margin: 0 !important;
  font-size: 0.93rem !important;
  font-weight: 600 !important;
  color: #1A1A1A !important;
}}

/* ── 바로 결과 보기 버튼 (.lg-skip-btn) ── */
button.lg-skip-btn {{
  background: transparent !important;
  border: 1.5px solid #E8E8E8 !important;
  box-shadow: none !important;
  color: #AAA !important;
  font-size: 0.76rem !important;
  font-weight: 500 !important;
  border-radius: 8px !important;
  transform: none !important;
  padding: 6px 18px !important;
  width: auto !important;
  min-width: 220px !important;
  justify-content: center !important;
  animation: none !important;
}}
button.lg-skip-btn:hover {{
  color: #A50034 !important;
  border-color: #A50034 !important;
  transform: none !important;
  box-shadow: none !important;
}}
button.lg-skip-btn > div {{
  justify-content: center !important;
  width: auto !important;
}}
button.lg-skip-btn p {{
  display: block !important;
  width: auto !important;
  text-align: center !important;
  font-size: 0.76rem !important;
  font-weight: 500 !important;
}}
/* ── 흰 컨테이너 박스 (설치공간 문항) ── */
div[data-testid="stVerticalBlockBorderWrapper"] {{
  border: 1.5px solid #E8E8E8 !important;
  border-radius: 16px !important;
  background: #FFFFFF !important;
  box-shadow: 0 2px 10px rgba(0,0,0,0.045) !important;
  padding: 8px 4px !important;
  margin-bottom: 0 !important;
}}
/* 흰 컨테이너 안의 primary 버튼 — 우측 정렬 + 콤팩트 */
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stButton"]:has(button[data-testid="stBaseButton-primary"]) {{
  display: flex !important;
  justify-content: flex-end !important;
}}
div[data-testid="stVerticalBlockBorderWrapper"] button[data-testid="stBaseButton-primary"] {{
  width: auto !important;
  min-width: 0 !important;
  padding-left: 28px !important;
  padding-right: 28px !important;
}}

/* ── 하단 내비게이션 ── */
.lg-bottom-nav {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 24px;
}}
.lg-bottom-nav-right {{
  display: flex;
  align-items: center;
  gap: 8px;
}}

/* ── 뒤로가기 버튼 (.lg-back-btn) ── */
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
  width: auto !important;
  min-width: unset !important;
}}
button.lg-back-btn:hover {{
  color: #555 !important;
  border: none !important;
  box-shadow: none !important;
  transform: none !important;
}}
button.lg-back-btn > div {{
  width: auto !important;
  justify-content: flex-start !important;
}}
button.lg-back-btn p {{
  display: block !important;
  width: auto !important;
  text-align: left !important;
  font-size: 0.82rem !important;
  font-weight: 500 !important;
}}

/* 카드 간격 */
div[data-testid="stButton"] {{
  margin-bottom: 8px !important;
}}

/* ── 1번 질문: 라이프스타일 빅카드 ── */
button.lg-persona-btn {{
  height: 280px !important;
  min-height: 286px !important;
  border-radius: 10px !important;
  padding: 22px 20px !important;
  align-items: flex-start !important;
  box-shadow: none !important;
}}
button.lg-persona-btn:hover {{
  box-shadow: 0 10px 26px rgba(0,0,0,0.07) !important;
}}
button.lg-persona-btn > div {{
  align-items: flex-start !important;
}}
button.lg-persona-btn p {{
  display: block !important;
  width: 100% !important;
}}
.lg-persona-content {{
  display: block;
  width: 100%;
  text-align: left;
}}
.lg-persona-icon {{
  display: flex;
  align-items: center;
  justify-content: center;
  width: 54px;
  height: 54px;
  border-radius: 50%;
  margin-bottom: 16px;
}}
.lg-persona-title {{
  display: block;
  color: #171717;
  font-size: 1rem;
  font-weight: 800;
  line-height: 1.35;
  margin-bottom: 9px;
}}
.lg-persona-desc {{
  display: block;
  color: #4F4F4F;
  font-size: 0.82rem;
  font-weight: 500;
  line-height: 1.55;
  min-height: 40px;
  margin-bottom: 16px;
}}
.lg-persona-chips {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px 7px;
}}
.lg-persona-chip {{
  display: inline-flex;
  align-items: center;
  min-height: 27px;
  border: 1px solid #D7D7D7;
  border-radius: 999px;
  background: #FFFFFF;
  color: #4D4D4D;
  padding: 4px 11px;
  font-size: 0.74rem;
  font-weight: 600;
  line-height: 1.25;
  word-break: keep-all;
}}

/* ── 바로 결과 보기 버튼 — 중앙 정렬 오버라이드 ── */
button.lg-skip-btn {{
  justify-content: center !important;
}}
button.lg-skip-btn > div {{
  justify-content: center !important;
  width: auto !important;
}}
button.lg-skip-btn p {{
  display: block !important;
  width: auto !important;
  text-align: center !important;
  justify-content: center !important;
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
.cs-chip.is-hidden {{
  display: none !important;
}}
.cs-dot {{
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid rgba(0,0,0,0.12);
  flex-shrink: 0;
  overflow: hidden;
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
.cs-material-select {{
  min-width: 150px;
  max-width: 100%;
  border: 1.5px solid #E8E8E8;
  border-radius: 10px;
  background: #FFFFFF;
  color: #333;
  font-family: 'Pretendard', 'Apple SD Gothic Neo', sans-serif;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 6px 30px 6px 10px;
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml;charset=utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23888780' stroke-width='1.5' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 10px;
}}
.cs-material-select:focus {{
  outline: none;
  border-color: #A50034;
  box-shadow: 0 0 0 2px rgba(165,0,52,0.08);
}}
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

/* ── 사이드바 페이지 네비게이션 숨김 (일반 사용자에게 admin 링크 미노출) ── */
[data-testid="stSidebarNav"], [data-testid="stSidebar"] {{
  display: none !important;
}}

/* ── Top 5 비교 섹션 ── */
.lg-compare-box {{
  margin: 22px 0 18px;
  padding: 18px;
  border: 1.5px solid #E8E8E8;
  border-radius: 12px;
  background: #FAFAFA;
}}
.lg-compare-title {{
  margin: 0 0 4px;
  color: #111;
  font-size: 1rem;
  font-weight: 800;
  letter-spacing: 0;
}}
.lg-compare-sub {{
  margin: 0;
  color: #888;
  font-size: 0.76rem;
  line-height: 1.45;
}}
.lg-compare-table-wrap {{
  width: 100%;
  overflow-x: auto;
  margin-top: 12px;
  border: 1px solid #ECECEC;
  border-radius: 10px;
  background: #FFFFFF;
}}
.lg-compare-table {{
  width: 100%;
  min-width: 620px;
  border-collapse: collapse;
  font-size: 0.76rem;
}}
.lg-compare-table th,
.lg-compare-table td {{
  padding: 9px 11px;
  border-bottom: 1px solid #EFEFEF;
  vertical-align: top;
  text-align: left;
  line-height: 1.45;
}}
.lg-compare-table tr:last-child th,
.lg-compare-table tr:last-child td {{
  border-bottom: 0;
}}
.lg-compare-table th {{
  width: 24%;
  background: #F7F7F7;
  color: #777;
  font-weight: 800;
  white-space: nowrap;
}}
.lg-compare-table td {{
  width: 38%;
  color: #333;
  overflow-wrap: anywhere;
}}
.lg-compare-table thead th {{
  background: #FFF5F7;
  color: #A50034;
  font-size: 0.72rem;
}}
.lg-compare-table tr.diff-row th,
.lg-compare-table tr.diff-row td {{
  background: #FFF9EC;
}}
.lg-compare-table tr.diff-row th {{
  color: #A05A00;
}}
.lg-diff-badge {{
  display: inline-flex;
  align-items: center;
  margin-left: 6px;
  padding: 2px 6px;
  border-radius: 999px;
  background: #FFE6B8;
  color: #8A4B00;
  font-size: 0.58rem;
  font-weight: 800;
  vertical-align: middle;
}}

/* ── LG 결과 화면 리디자인 ── */
.lg-result-wrap {{
  --lg-red: #A50034;
  --lg-red-soft: #FFF5F7;
  --lg-red-border: #F4C0D1;
  --text-primary: #2C2C2A;
  --text-secondary: #5F5E5A;
  --text-tertiary: #888780;
  --border: #E5E5E5;
  --border-soft: #F0F0F0;
  --bg-soft: #FAFAFA;
  color: var(--text-primary);
  font-size: 0.92rem;
}}
.lg-result-kicker {{
  font-size: 0.6rem;
  font-weight: 700;
  color: var(--lg-red);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: 0.22rem;
}}
.lg-result-title {{
  font-size: 1.18rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.25;
  margin: 0;
}}
.lg-result-subtitle {{
  font-size: 0.72rem;
  color: var(--text-secondary);
  margin: 0.25rem 0 0.75rem;
  line-height: 1.35;
}}
.lg-result-card {{
  background: #fff;
  border-radius: 12px;
  border: 2px solid var(--lg-red);
  padding: 1.85rem 0.92rem 0.92rem;
  margin: 0;
  position: relative;
  animation: lgFadeUp 0.25s ease both;
}}
.lg-best-badge {{
  position: absolute;
  top: -15px;
  left: 16px;
  background: var(--lg-red);
  color: #fff;
  font-size: 0.6rem;
  font-weight: 700;
  padding: 5px 14px;
  border-radius: 999px;
  letter-spacing: 0.04em;
  z-index: 3;
}}
.lg-product-header {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  margin: 2px 0 10px;
}}
.lg-product-code {{
  font-size: 0.64rem;
  color: var(--text-tertiary);
  margin: 0 0 2px;
}}
.lg-product-code-inline {{
  display: inline-block;
  margin-left: 0.45rem;
  color: var(--text-tertiary);
  font-size: 0.64rem !important;
  line-height: 1.2 !important;
  font-weight: 500 !important;
  white-space: nowrap;
  vertical-align: baseline;
}}
.lg-product-name {{
  font-size: 0.9rem;
  font-weight: 700;
  margin: 0 0 4px;
  line-height: 1.24;
  overflow-wrap: anywhere;
  word-break: keep-all;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}}
.lg-product-spec {{
  font-size: 0.68rem;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.32;
  overflow-wrap: anywhere;
  word-break: keep-all;
}}
.lg-fit-score {{
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: 2.5px solid var(--lg-red);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  background: var(--lg-red-soft);
  flex-shrink: 0;
}}
.lg-fit-num {{
  font-size: 0.94rem;
  font-weight: 800;
  color: var(--lg-red);
  line-height: 1;
}}
.lg-fit-label {{
  font-size: 0.52rem;
  color: var(--lg-red);
  margin-top: 1px;
}}
.lg-ai-box {{
  background: linear-gradient(135deg, var(--lg-red-soft) 0%, var(--bg-soft) 100%);
  border-radius: 10px;
  padding: 9px 10px;
  margin-bottom: 8px;
  border: 0.5px solid var(--lg-red-border);
}}
.lg-ai-label-wrap {{
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 5px;
}}
.lg-ai-dot {{
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--lg-red);
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 0.62rem;
}}
.lg-ai-label {{
  font-size: 0.6rem;
  font-weight: 700;
  color: var(--lg-red);
  letter-spacing: 0.04em;
}}
.lg-ai-text {{
  font-size: 0.68rem;
  line-height: 1.45;
  color: var(--text-primary);
  margin: 0;
  overflow-wrap: anywhere;
  word-break: keep-all;
}}
.lg-ai-text strong {{
  color: var(--lg-red);
  font-weight: 700;
}}
.lg-section {{
  background: var(--bg-soft);
  border-radius: 8px;
  padding: 8px 10px;
  margin-bottom: 8px;
}}
.lg-section-label {{
  font-size: 0.6rem;
  color: var(--text-tertiary);
  margin: 0 0 6px;
  letter-spacing: 0.03em;
  font-weight: 700;
}}
.lg-tag-wrap {{
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}}
.lg-tag {{
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.63rem;
  padding: 3px 7px;
  background: #fff;
  border: 0.5px solid #D4D4D4;
  border-radius: 12px;
  color: var(--text-primary);
  max-width: 100%;
  overflow-wrap: anywhere;
}}
.lg-tag::before {{
  content: "✓";
  color: #639922;
  font-weight: 800;
}}
.lg-tag-highlight {{
  background: var(--lg-red-soft);
  border-color: var(--lg-red-border);
  color: var(--lg-red);
  font-weight: 700;
}}
.lg-tag-highlight::before {{
  content: "✦";
  color: var(--lg-red);
}}
.lg-review-head {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  gap: 8px;
}}
.lg-rating {{
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}}
.lg-rating-num {{
  font-size: 0.68rem;
  font-weight: 700;
}}
.lg-rating-stars {{
  color: #F0997B;
  font-size: 0.58rem;
  letter-spacing: -1px;
}}
.lg-rating-count {{
  font-size: 0.58rem;
  color: var(--text-tertiary);
}}
.lg-bar-list {{
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 6px;
}}
.lg-bar-row {{
  display: flex;
  align-items: center;
  gap: 8px;
}}
.lg-bar-label {{
  font-size: 0.6rem;
  width: 58px;
  color: var(--text-secondary);
}}
.lg-bar-track {{
  flex: 1;
  height: 3px;
  background: #F1EFE8;
  border-radius: 2px;
  overflow: hidden;
}}
.lg-bar-fill {{
  height: 100%;
  background: #639922;
}}
.lg-bar-fill.amber {{
  background: #BA7517;
}}
.lg-bar-num {{
  font-size: 0.56rem;
  color: var(--text-secondary);
  width: 22px;
  text-align: right;
}}
.lg-keywords {{
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}}
.lg-keyword {{
  font-size: 0.56rem;
  padding: 2px 6px;
  border-radius: 8px;
  background: #EAF3DE;
  color: #3B6D11;
}}
.lg-color-section {{
  margin-bottom: 8px;
}}
.lg-result-wrap .cs-section {{
  border-top: 0;
  margin-top: 0;
  padding-top: 0;
}}
.lg-result-wrap .cs-row-label {{
  color: var(--text-tertiary);
  font-size: 0.6rem;
  letter-spacing: 0.03em;
  text-transform: none;
}}
.lg-result-wrap .cs-chip {{
  border-radius: 16px;
  background: #fff;
  color: var(--text-primary);
  font-size: 0.63rem;
  padding: 4px 9px 4px 7px;
  max-width: 100%;
  overflow-wrap: anywhere;
}}
.lg-result-wrap .cs-chip.active {{
  border: 2px solid var(--lg-red);
  background: var(--lg-red-soft);
  color: var(--lg-red);
}}
.lg-price-row {{
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 8px;
  padding-top: 8px;
  border-top: 0.5px solid var(--border);
}}
.lg-price-label {{
  font-size: 0.56rem;
  color: var(--text-tertiary);
  margin: 0 0 2px;
}}
.lg-price-num {{
  font-size: 1rem;
  font-weight: 800;
  margin: 0;
  color: var(--text-primary);
}}
.lg-price-suffix {{
  font-size: 0.68rem;
  color: var(--text-secondary);
  font-weight: 500;
}}
.lg-link-btn {{
  padding: 6px 9px;
  border: 0.5px solid #D4D4D4;
  background: #fff;
  border-radius: 8px;
  font-size: 0.62rem;
  color: var(--text-primary);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
}}
.lg-link-btn.primary {{
  border: 0;
  background: var(--lg-red);
  color: #fff;
  font-weight: 700;
}}
.lg-carousel {{
  position: relative;
}}
.lg-carousel-viewport {{
  overflow: hidden;
  border-radius: 12px;
  padding-top: 16px;
}}
.lg-carousel-track {{
  display: flex;
  transition: transform 240ms ease;
}}
.lg-carousel-slide {{
  flex: 0 0 100%;
  min-width: 0;
}}
.lg-carousel-nav {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 7px;
  gap: 8px;
}}
.lg-arrow {{
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--lg-red);
  display: grid;
  place-items: center;
  font-size: 1.05rem;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  user-select: none;
  padding: 0;
}}
.lg-arrow.disabled {{
  opacity: 0.28;
  cursor: default;
}}
.lg-slide-count {{
  flex: 1;
  text-align: center;
  font-size: 0.66rem;
  font-weight: 700;
  color: var(--text-tertiary);
}}
.lg-dots {{
  display: flex;
  justify-content: center;
  gap: 5px;
  margin-top: 6px;
}}
.lg-dot {{
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #E0E0E0;
  border: 0;
  padding: 0;
  cursor: pointer;
}}
.lg-dot.active {{
  background: var(--lg-red);
}}
.lg-footer-actions {{
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 16px;
}}

/* ── 애니메이션 ── */
@keyframes lgFadeUp {{
  from {{ opacity: 0; transform: translateY(10px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}

/* ── 설문 배너 (2열 반응형) ── */
.lg-survey-banner-wrap {{
  background: #FFFFFF;
  border: 1.5px solid #E8E8E8;
  border-radius: 14px;
  padding: 16px 22px;
  margin-bottom: 14px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  animation: lgFadeUp 0.25s ease both;
}}
.lg-survey-banner-title {{
  font-size: 0.92rem;
  font-weight: 700;
  color: #111;
  margin: 0 0 3px;
  word-break: keep-all;
}}
.lg-survey-banner-desc {{
  font-size: 0.77rem;
  color: #888;
  line-height: 1.55;
  margin: 0;
  word-break: keep-all;
}}
.lg-survey-completed {{
  background: #F5FFF5;
  border: 1.5px solid #C3E6CB;
  border-radius: 14px;
  padding: 13px 22px;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.84rem;
  font-weight: 600;
  color: #2E7D32;
}}
/* 배너 내 Streamlit 컬럼 패딩 제거 */
.lg-survey-banner-wrap + div [data-testid="stHorizontalBlock"] {{
  gap: 12px !important;
}}

/* ── 설문 배너 버튼 — 우측 중앙 정렬 ── */
div[data-testid="stHorizontalBlock"]:has(.lg-survey-banner-wrap) {{
  align-items: center !important;
}}

/* ── 설문 모달 내부 ── */
.sv-section-title {{
  font-size: 0.68rem;
  font-weight: 800;
  color: #A50034;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  margin: 14px 0 8px;
  padding-bottom: 5px;
  border-bottom: 1.5px solid #F0F0F0;
}}
.sv-q-block {{
  margin-bottom: 14px;
}}
.sv-q-label {{
  font-size: 0.86rem;
  font-weight: 600;
  color: #1A1A1A;
  line-height: 1.5;
  margin: 0 0 8px;
  word-break: keep-all;
  overflow-wrap: break-word;
  display: block;
}}
/* 리커트 원형 버튼 */
div[data-testid="stDialog"] [data-testid="stPills"] {{
  gap: 6px !important;
}}
div[data-testid="stDialog"] [data-testid="stPills"] button {{
  min-width: 40px !important;
  width: 40px !important;
  height: 40px !important;
  border-radius: 50% !important;
  padding: 0 !important;
  font-size: 0.88rem !important;
  font-weight: 700 !important;
  transition: transform 150ms, border-color 150ms, background 150ms !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}}
div[data-testid="stDialog"] [data-testid="stPills"] button:not([aria-pressed="true"]) {{
  border: 2px solid #D0D0D0 !important;
  background: #fff !important;
  color: #555 !important;
}}
div[data-testid="stDialog"] [data-testid="stPills"] button:not([aria-pressed="true"]):hover {{
  border-color: #A50034 !important;
  color: #A50034 !important;
  transform: scale(1.07) !important;
}}
div[data-testid="stDialog"] [data-testid="stPills"] button[aria-pressed="true"] {{
  background: #A50034 !important;
  border-color: #A50034 !important;
  color: #fff !important;
}}
/* 텍스트 영역 */
div[data-testid="stDialog"] div[data-testid="stTextArea"] {{
  margin-top: 0 !important;
}}
div[data-testid="stDialog"] div[data-testid="stTextArea"] textarea {{
  border: 1.5px solid #E8E8E8 !important;
  border-radius: 10px !important;
  font-size: 0.84rem !important;
  padding: 10px 14px !important;
  resize: vertical !important;
}}
div[data-testid="stDialog"] div[data-testid="stTextArea"] textarea:focus {{
  border-color: #A50034 !important;
  box-shadow: 0 0 0 3px rgba(165,0,52,0.07) !important;
  outline: none !important;
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
  const PERSONA_COLORS = {{
    freshness: ['#E0F5EA', '#2C9B73'],
    hygiene: ['#E8F2FF', '#3478D9'],
    saving: ['#FFF2D8', '#C47A16'],
    storage: ['#EEE7FF', '#7353D9'],
    smart_home: ['#FFE8E7', '#C0473B'],
    interior: ['#FFE6F1', '#C84A7A'],
    default: ['#F5F5F7', '#555555'],
  }};
  const PERSONA_EMOJI = {{
    freshness: '🍃',
    hygiene: '✨',
    saving: '⚡',
    storage: '🛒',
    smart_home: '🤖',
    interior: '🎨',
  }};

  function escapeHtml(value) {{
    return String(value || '').replace(/[&<>"']/g, function(ch) {{
      return ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}})[ch];
    }});
  }}

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
    if (parentDoc.getElementById('lg-runtime-styles-v2')) return;
    const s = parentDoc.createElement('style');
    s.id = 'lg-runtime-styles-v2';
    s.textContent = [
      /* ── 선택지 카드 — option 전용 (skip/back 제외) ── */
      'button[data-testid="stBaseButton-secondary"]:not(.lg-skip-btn):not(.lg-back-btn){{',
      '  background:#FFFFFF!important;border:1.5px solid #E8E8E8!important;',
      '  border-radius:14px!important;box-shadow:0 2px 10px rgba(0,0,0,.045)!important;',
      '  justify-content:flex-start!important;padding:16px 20px!important;',
      '  width:100%!important;align-items:center!important;',
      '  transition:border-color .18s,box-shadow .18s,transform .18s!important;',
      '}}',
      'button[data-testid="stBaseButton-secondary"]:not(.lg-skip-btn):not(.lg-back-btn):hover{{',
      '  border-color:#A50034!important;box-shadow:0 8px 24px rgba(165,0,52,.09)!important;',
      '  transform:translateY(-2px)!important;background:#FFFFFF!important;',
      '}}',
      'button[data-testid="stBaseButton-secondary"]:not(.lg-skip-btn):not(.lg-back-btn)>div{{',
      '  width:100%!important;display:flex!important;align-items:center!important;',
      '}}',
      'button[data-testid="stBaseButton-secondary"]:not(.lg-skip-btn):not(.lg-back-btn) p{{',
      '  text-align:left!important;width:100%!important;margin:0!important;',
      '}}',
      /* ── 바로 결과 보기 ── */
      'button.lg-skip-btn{{background:transparent!important;border:1.5px solid #E8E8E8!important;',
      '  box-shadow:none!important;color:#AAA!important;font-size:.76rem!important;',
      '  font-weight:500!important;border-radius:8px!important;transform:none!important;',
      '  padding:6px 18px!important;width:auto!important;min-width:220px!important;',
      '  justify-content:center!important;animation:none!important;}}',
      'button.lg-skip-btn:hover{{color:#A50034!important;border-color:#A50034!important;transform:none!important;}}',
      'button.lg-skip-btn>div{{justify-content:center!important;width:auto!important;}}',
      'button.lg-skip-btn p{{display:block!important;width:auto!important;text-align:center!important;font-size:.76rem!important;font-weight:500!important;}}',
      '[data-testid="stButton"]:has(button.lg-skip-btn){{display:flex!important;justify-content:center!important;}}',
      /* ── 뒤로가기 ── */
      'button.lg-back-btn{{background:transparent!important;border:none!important;',
      '  box-shadow:none!important;color:#AAA!important;font-size:.82rem!important;',
      '  font-weight:500!important;padding:4px 0!important;transform:none!important;',
      '  animation:none!important;width:auto!important;}}',
      'button.lg-back-btn:hover{{color:#555!important;border:none!important;box-shadow:none!important;transform:none!important;}}',
      'button.lg-back-btn>div{{width:auto!important;justify-content:flex-start!important;}}',
      'button.lg-back-btn p{{display:block!important;width:auto!important;text-align:left!important;font-size:.82rem!important;font-weight:500!important;}}',
      /* ── Primary ── */
      'button[data-testid="stBaseButton-primary"]{{',
      '  background:#A50034!important;border:none!important;',
      '  border-radius:10px!important;color:#fff!important;',
      '  font-weight:700!important;letter-spacing:.01em!important;',
      '}}',
      'button[data-testid="stBaseButton-primary"]:hover{{',
      '  background:#8A0029!important;transform:translateY(-1px)!important;',
      '  box-shadow:0 6px 18px rgba(165,0,52,.22)!important;',
      '}}',
      'button.lg-persona-btn{{height:340px!important;min-height:286px!important;border-radius:10px!important;padding:22px 20px!important;align-items:flex-start!important;box-shadow:none!important;}}',
      'button.lg-persona-btn:hover{{box-shadow:0 10px 26px rgba(0,0,0,.07)!important;}}',
      'button.lg-persona-btn>div{{align-items:flex-start!important;}}',
      '.lg-persona-content{{display:block;width:100%;text-align:left;}}',
      '.lg-persona-icon{{display:flex;align-items:center;justify-content:center;width:54px;height:54px;border-radius:50%;margin-bottom:16px;}}',
      '.lg-persona-title{{display:block;color:#171717;font-size:1rem;font-weight:800;line-height:1.35;margin-bottom:9px;}}',
      '.lg-persona-desc{{display:block;color:#4F4F4F;font-size:.82rem;font-weight:500;line-height:1.55;min-height:40px;margin-bottom:16px;}}',
      '.lg-persona-chips{{display:flex;flex-wrap:wrap;gap:6px 7px;}}',
      '.lg-persona-chip{{display:inline-flex;align-items:center;min-height:27px;border:1px solid #D7D7D7;border-radius:999px;background:#FFF;color:#4D4D4D;padding:4px 11px;font-size:.74rem;font-weight:600;line-height:1.25;word-break:keep-all;}}',
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
        /* 바로 결과 보기 / 모름·건너뛰기 — 보조 버튼 스타일, 아이콘 처리 제외 */
        if (rawText.includes('바로 결과') || rawText.includes('모름') || rawText.includes('건너뛰기')) {{
          btn.classList.add('lg-skip-btn');
          btn.style.width = 'auto';
          return;
        }}

        /* 이미 처리된 카드 건너뜀 */
        if (btn.dataset.lgDone === '1') return;

        const p = btn.querySelector('p');
        if (!p) return;

        const title = (p.textContent || '').trim();
        if (!title) return;
        const rawDesc = LABEL_DESCS[title] || '';
        const descParts = rawDesc.split('||');
        const desc = descParts[0] || '';
        const chips = descParts.length > 1
          ? descParts.slice(1).join('||').split('|').map(v => v.trim()).filter(Boolean)
          : [];
        const rawIKey = LABEL_ICONS[title];
        const hasIcon = rawIKey !== undefined;
        const iKey = rawIKey || 'default';
        const isPersona = chips.length > 0;

        /* 일반 카드 버튼 클래스 표시 */
        btn.classList.add('lg-option-btn');

        /* 인라인 스타일 직접 설정 (Emotion CSS를 확실히 오버라이드) */
        btn.style.justifyContent = 'flex-start';
        btn.style.padding = isPersona ? '22px 20px' : '16px 20px';
        if (isPersona) {{
          btn.classList.add('lg-persona-btn');
          btn.style.height = '340px';
          btn.style.minHeight = '286px';
          btn.style.alignItems = 'flex-start';
        }}

        /* MutationObserver 일시 중지 → DOM 수정 → 재개 */
        _paused = true;
        if (isPersona) {{
          const personaColor = PERSONA_COLORS[iKey] || PERSONA_COLORS.default;
          const chipHtml = chips
            .map(chip => '<span class="lg-persona-chip">' + escapeHtml(chip) + '</span>')
            .join('');
          p.style.cssText = 'display:block!important;width:100%!important;margin:0!important;';
          p.innerHTML =
            '<span class="lg-persona-content">'
            + '<span class="lg-persona-icon" style="background:' + personaColor[0] + ';color:' + personaColor[1] + ';font-size:1.55rem;">'
            + (PERSONA_EMOJI[iKey] || makeSvg(iKey)) + '</span>'
            + '<span class="lg-persona-title">' + escapeHtml(title) + '</span>'
            + '<span class="lg-persona-desc">' + escapeHtml(desc) + '</span>'
            + '<span class="lg-persona-chips">' + chipHtml + '</span>'
            + '</span>';
        }} else {{
          p.style.cssText = 'width:100%!important;display:flex!important;'
            + 'justify-content:flex-start!important;align-items:center!important;'
            + 'margin:0!important;gap:14px!important;';
          p.innerHTML =
            '<span style="display:flex;align-items:center;justify-content:center;'
            + 'width:40px;height:40px;min-width:40px;border-radius:10px;'
            + 'background:#F5F5F7;color:#555555;flex-shrink:0;" class="lg-icon-box">'
            + makeSvg(iKey) + '</span>'
            + '<span style="flex:1;min-width:0;text-align:left;">'
            + '<span style="display:block;font-size:0.93rem;font-weight:700;'
            + 'color:#111;line-height:1.3;">' + escapeHtml(title) + '</span>'
            + (desc
                ? '<span style="display:block;font-size:0.78rem;font-weight:400;'
                  + 'color:#999;margin-top:3px;line-height:1.3;">' + escapeHtml(desc) + '</span>'
                : '')
            + '</span>'
            + '<span style="color:#D0D0D0;font-size:1.1rem;flex-shrink:0;margin-left:auto;">›</span>';
        }}
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
    lifestyle_label = E.LIFESTYLE_LABELS.get(ans.get("lifestyle"))
    if lifestyle_label:
        crumb_data.append(("lifestyle", lifestyle_label))
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

    space_ans = ans.get("space")
    if space_ans:
        if space_ans == "skip":
            crumb_data.append(("space", "설치공간 건너뜀"))
        elif isinstance(space_ans, dict):
            parts = []
            if space_ans.get("w"):
                parts.append(f"폭 {space_ans['w']}mm")
            if space_ans.get("h"):
                parts.append(f"높이 {space_ans['h']}mm")
            if space_ans.get("d"):
                parts.append(f"깊이 {space_ans['d']}mm")
            if parts:
                crumb_data.append(("space", " · ".join(parts)))

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


def render_progress(q: str):
    if q == "result":
        return

    labels = {
        "lifestyle": "라이프스타일",
        "install": "설치 타입",
        "household": "사용 인원",
        "cooking": "요리 빈도",
        "door_style": "도어 방식",
        "space": "설치 공간",
        "features": "추가 기능",
    }
    steps = ["lifestyle", "install"]
    if ans.get("install") != "빌트인":
        steps.extend(["household", "cooking"])
        if q == "door_style" or "door_style" in ans or "door_style" in st.session_state.get("history", []):
            steps.append("door_style")
        elif ans.get("household") and ans.get("cooking"):
            cand_now, _ = E.filter_candidates(PRODUCTS, ans)
            if E.needs_door_style(cand_now, ans):
                steps.append("door_style")
    if ans.get("install") != "빌트인":
        steps.append("space")

    steps.append("features")

    if q not in steps:
        steps.append(q)
    total = max(1, len(steps))
    current = steps.index(q) + 1
    pct = min(100, max(0, round(current / total * 100)))
    st.markdown(
        f"""
        <div class="lg-progress-wrap">
          <div class="lg-progress-meta">
            <span>질문 진행률</span>
            <span><strong>{current}</strong> / {total} · {_html(labels.get(q, "질문"))}</span>
          </div>
          <div class="lg-progress-track">
            <div class="lg-progress-fill" style="width:{pct}%;"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def q_bubble(text: str):
    st.markdown(f'<div class="q-bubble">{text}</div>', unsafe_allow_html=True)


def _select_option(q_id: str, opt):
    st.session_state.click_count += 1
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


def option_buttons(q_id: str):
    """ui_config 기반 선택지 카드 렌더링.
    라벨만 버튼에 표시하고, JS가 아이콘·설명을 후처리합니다."""
    q_cfg = CFG.questions.get(q_id)
    if not q_cfg:
        return
    q_bubble(q_cfg.text)
    if q_id == "lifestyle":
        for row_start in range(0, len(q_cfg.options), 3):
            cols = st.columns(3, gap="medium")
            for col, opt in zip(cols, q_cfg.options[row_start:row_start + 3]):
                with col:
                    if st.button(opt.label, key=f"opt_{q_id}_{opt.value}", use_container_width=True):
                        _select_option(q_id, opt)
        return

    for opt in q_cfg.options:
        if st.button(opt.label, key=f"opt_{q_id}_{opt.value}", use_container_width=True):
            _select_option(q_id, opt)


def show_skip_btn():
    """현재까지 답한 조건만으로 바로 결과 보기 — 보조 버튼."""
    if not ans:   # 아직 아무것도 답하지 않은 첫 화면엔 표시 안 함
        return
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([3, 4, 3])
    with mid:
        if st.button("지금 바로 결과 보기 →", key="skip_to_result", use_container_width=False):
            st.session_state.click_count += 1
            st.session_state.force_result = True
            st.rerun()


_LIKERT_NUMS = ["1", "2", "3", "4", "5"]


def _sv_q(key: str, text: str) -> str | None:
    """설문 문항 1개 렌더링 — 질문 텍스트 + pills 숫자 선택."""
    st.markdown(f'<div class="sv-q-block"><span class="sv-q-label">{text}</span></div>', unsafe_allow_html=True)
    val = st.pills(
        key,
        _LIKERT_NUMS,
        selection_mode="single",
        default=None,
        label_visibility="collapsed",
        key=f"sv_{key}",
    )
    return val


@st.dialog("서비스 이용 경험 설문", width="large")
def open_survey_dialog():
    st.markdown(
        "<p style='font-size:0.83rem;color:#666;line-height:1.6;margin:0 0 6px;'>"
        "추천 결과를 확인하신 후 서비스 이용 경험에 대한 간단한 설문에 참여해 주세요. "
        "응답은 익명으로 처리되며 약 1분 정도 소요됩니다."
        "</p>"
        "<p style='font-size:0.74rem;color:#aaa;margin:0 0 4px;'>"
        "1 = 전혀 그렇지 않다 &nbsp;·&nbsp; 5 = 매우 그렇다"
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sv-section-title">탐색 경험</div>', unsafe_allow_html=True)
    q1 = _sv_q("q1", "Q1. 원하는 냉장고를 쉽게 찾을 수 있었다.")
    q2 = _sv_q("q2", "Q2. 어떤 제품을 선택해야 할지 탐색 과정이 명확했다.")
    q3 = _sv_q("q3", "Q3. 제품을 탐색하는 과정이 복잡하지 않았다.")

    st.markdown('<div class="sv-section-title">의사결정 지원</div>', unsafe_allow_html=True)
    q4 = _sv_q("q4", "Q4. 제품 간 차이점을 이해하기 쉬웠다.")
    q5 = _sv_q("q5", "Q5. 제품 선택에 필요한 정보를 충분히 제공받았다.")
    q6 = _sv_q("q6", "Q6. 이 서비스는 제품 선택에 도움이 되었다.")

    st.markdown('<div class="sv-section-title">선택 확신도</div>', unsafe_allow_html=True)
    q7 = _sv_q("q7", "Q7. 최종 선택한 제품이 나의 요구에 적합하다고 생각한다.")
    q8 = _sv_q("q8", "Q8. 실제 구매 상황에서도 이 제품을 선택할 의향이 있다.")

    st.markdown('<div class="sv-section-title">주관식</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="sv-q-block">'
        '<span class="sv-q-label">Q9. 서비스 이용 중 가장 도움이 되었던 기능이나 정보는 무엇이었습니까?</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    q9 = st.text_area(
        "Q9 입력", placeholder="자유롭게 작성해 주세요.",
        label_visibility="collapsed", key="sv_q9_ta", height=88,
    )

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="sv-q-block">'
        '<span class="sv-q-label">Q10. 개선이 필요하다고 생각한 부분이 있다면 자유롭게 작성해 주세요.</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    q10 = st.text_area(
        "Q10 입력", placeholder="자유롭게 작성해 주세요.",
        label_visibility="collapsed", key="sv_q10_ta", height=88,
    )

    likert_vals = [q1, q2, q3, q4, q5, q6, q7, q8]
    all_answered = all(v is not None for v in likert_vals)

    if not all_answered:
        st.caption("📌 Q1~Q8의 모든 문항에 응답하면 제출 버튼이 활성화됩니다.")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if st.button("제출하기", type="primary", use_container_width=True,
                 disabled=not all_answered, key="sv_submit"):
        DB.log_survey_response(
            session_id=st.session_state.session_id,
            responses={
                "q1": int(q1) if q1 else None,
                "q2": int(q2) if q2 else None,
                "q3": int(q3) if q3 else None,
                "q4": int(q4) if q4 else None,
                "q5": int(q5) if q5 else None,
                "q6": int(q6) if q6 else None,
                "q7": int(q7) if q7 else None,
                "q8": int(q8) if q8 else None,
                "q9": q9.strip() if q9 else None,
                "q10": q10.strip() if q10 else None,
            },
        )
        st.session_state._survey_submitted = True
        st.session_state._survey_open = False
        st.rerun()


def render_survey_banner():
    """결과 페이지 상단 설문 배너 — 2열 레이아웃."""
    if st.session_state._survey_submitted:
        st.markdown(
            '<div class="lg-survey-completed">'
            '<span style="font-size:1.1rem;">✅</span>'
            '<span>설문 참여 완료 — 소중한 의견 감사합니다.</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    left_col, right_col = st.columns([3, 1])
    with left_col:
        st.markdown(
            '<div class="lg-survey-banner-wrap">'
            '<div class="lg-survey-banner-title">📝 서비스 이용 경험 설문</div>'
            '<p class="lg-survey-banner-desc">'
            '추천 결과를 확인하신 후 간단한 설문에 참여해 주세요.<br>'
            '응답은 연구 목적으로만 사용되며 약 1분 소요됩니다.'
            '</p>'
            '</div>',
            unsafe_allow_html=True,
        )
    with right_col:
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        if st.button("설문 참여하기", key="survey_open_btn", type="primary", use_container_width=True):
            open_survey_dialog()


def compute_fit_score(p: dict, ans: dict, applied_tier) -> float:
    """UI 표시용 종합 적합도 (0.0~1.0). 후보 필터링 로직은 engine.py 그대로."""
    parts: list[tuple[float, float]] = []   # (score, weight)

    # ① 용량 적합도 (40%) — 목표 tier와의 거리
    if applied_tier and p.get("total_l"):
        actual = E.tier_index(p["total_l"]) or applied_tier
        diff = abs(actual - applied_tier)
        vol = max(0.0, 1.0 - diff * 0.22)
        parts.append((vol, 0.40))

    # ② 라이프스타일/원하는 기능 매칭 (35%)
    wanted = set(ans.get("wanted_features", [])) | E.lifestyle_feature_set(ans)
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

    # 기능 — 라이프스타일/원하는 기능 충족 비율
    wanted = set(ans.get("wanted_features", [])) | E.lifestyle_feature_set(ans)
    if wanted:
        hit = wanted & p.get("features", set())
        f_score = round(len(hit) / len(wanted) * 100)
        if f_score == 100:
            bullet = "라이프스타일에 맞는 기능을 모두 갖췄어요"
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
            swatch_style = _color_swatch_style(cname)
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
                f' data-mat="{v_mat}"'
                f' data-url="{_lge_product_url(v_code)}">'
                f'<span class="cs-dot" style="{swatch_style}"></span>'
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
        swatch_style = _color_swatch_style(single_color)
        mat_display = (
            f'<span class="cs-info-sep">·</span>'
            f'<span class="cs-info-label">재질</span>'
            f'<span class="cs-info-val" id="{cmat_id}">{init_mat}</span>'
        ) if init_mat else f'<span id="{cmat_id}"></span>'
        sku_html = (
            '<div class="cs-section">'
            '<div class="cs-chips" style="margin-bottom:10px;">'
            f'<span class="cs-chip active" style="cursor:default;">'
            f'<span class="cs-dot" style="{swatch_style}"></span>'
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
      <div class="res-spec"><span id="{ccode_id}-spec">{init_code}</span> &nbsp;·&nbsp; {p.get('install','—')} &nbsp;·&nbsp;
        {p.get('doors','—')} &nbsp;·&nbsp; 총 {p.get('total_l') or '—'}L &nbsp;·&nbsp; 에너지 {p.get('energy') or '—'}등급
        &nbsp;·&nbsp; {p.get('size_raw','—')}</div>
      <div class="res-price"><span id="{cprc_id}">{disp_price}</span></div>
      <div class="res-chips">{chips_html}</div>
      {sku_html}
      {bullets_html}
      {bars_html}
    </div>
    """, unsafe_allow_html=True)


def render_lg_result_page(scored: list[tuple[float, int, dict]], ans: dict, applied_tier, cand_count: int, db_total: int) -> None:
    """Render the final result with the LG result-screen visual system."""
    lifestyle = E.LIFESTYLE_LABELS.get(ans.get("lifestyle"), "고객")
    q_count = len(st.session_state.get("history", []))
    total = len(scored)
    carousel_id = "lgc-" + "".join(ch for ch in st.session_state.session_id if ch.isalnum())[:10]
    slides = "".join(
        f'<section class="lg-carousel-slide">{_lg_result_card_html(fit, rank, p, ans, applied_tier, total)}</section>'
        for fit, rank, p in scored
    )
    nav = _lg_carousel_nav(total, carousel_id)
    dots = "".join(
        f'<button class="lg-dot{" active" if idx == 0 else ""}" type="button" data-carousel="{carousel_id}" data-index="{idx}" aria-label="{idx + 1}번 추천 보기"></button>'
        for idx in range(total)
    )

    html = "".join(
        [
            '<div class="lg-result-wrap">',
            '<div style="margin-bottom:1rem;">',
            '<div class="lg-result-kicker">LG Electronics</div>',
            f'<h2 class="lg-result-title">{_html(lifestyle)}님께 추천드려요</h2>',
            f'<p class="lg-result-subtitle">답변하신 {q_count}가지 조건을 바탕으로 {db_total}개 모델 중 후보 {cand_count}개를 정리했어요.</p>',
            "</div>",
            f'<div class="lg-carousel" id="{carousel_id}" data-index="0" data-total="{total}">',
            '<div class="lg-carousel-viewport"><div class="lg-carousel-track">',
            slides,
            "</div></div>",
            nav,
            f'<div class="lg-dots">{dots}</div>',
            "</div>",
            "</div>",
        ]
    )
    st.markdown(html, unsafe_allow_html=True)


def _lg_result_card_html(fit: float, rank: int, p: dict, ans: dict, applied_tier, total: int) -> str:
    sku_html, init_code, init_mat, init_price = _lg_sku_html(p, rank)
    reasons = _lg_reason_tags(p, ans, applied_tier)
    ai_text = _lg_ai_text(p, ans, applied_tier, reasons)
    feature_chips = _lg_feature_tags(p, ans)
    price_html = _lg_price_html(init_price or p.get("price_min"))
    product_url = _lge_product_url(init_code)
    badge = "BEST MATCH" if rank == 1 else f"TOP {rank} / {total}"
    return "".join(
        [
            '<div class="lg-result-card">',
            f'<div class="lg-best-badge">{badge}</div>',
            '<div class="lg-product-header">',
            '<div style="flex:1;min-width:0;">',
            f'<h3 class="lg-product-name">{_html(p.get("name") or "LG 냉장고")}<span class="lg-product-code-inline" id="card-code-{rank}">{_html(init_code)}</span></h3>',
            f'<p class="lg-product-spec" id="card-spec-{rank}">{_html(_lg_spec_line(p, init_mat))}</p>',
            "</div>",
            "</div>",
            '<div class="lg-ai-box">',
            '<div class="lg-ai-label-wrap">',
            '<div class="lg-ai-dot">✦</div>',
            '<span class="lg-ai-label">LG 매니저 AI</span>',
            "</div>",
            f'<p class="lg-ai-text">{ai_text}</p>',
            "</div>",
            '<div class="lg-section">',
            '<p class="lg-section-label">왜 이 모델을 추천하나요?</p>',
            f'<div class="lg-tag-wrap">{reasons}{feature_chips}</div>',
            "</div>",
            f'<div class="lg-color-section">{sku_html}</div>',
            '<div class="lg-price-row">',
            "<div>",
            '<p class="lg-price-label">최저가</p>',
            f'<p class="lg-price-num"><span id="card-price-{rank}">{price_html}</span><span class="lg-price-suffix">~</span></p>',
            "</div>",
            '<div style="display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;">',
            '<span class="lg-link-btn">자세히</span>',
            f'<a class="lg-link-btn primary" id="card-link-{rank}" href="{_html(product_url)}" target="_blank" rel="noopener noreferrer">LG.com에서 보기 →</a>',
            "</div>",
            "</div>",
            "</div>",
        ]
    )


def _lg_carousel_nav(total: int, carousel_id: str) -> str:
    return (
        '<div class="lg-carousel-nav">'
        f'<button class="lg-arrow disabled" type="button" data-carousel="{carousel_id}" data-dir="-1" aria-label="이전 추천 보기" disabled>‹</button>'
        f'<div class="lg-slide-count">추천 <span class="lg-current">1</span> / {total}</div>'
        f'<button class="lg-arrow" type="button" data-carousel="{carousel_id}" data-dir="1" aria-label="다음 추천 보기">›</button>'
        '</div>'
    )


def _html(value) -> str:
    return escape(str(value or ""))


def _lg_spec_line(p: dict, material: str | None = None) -> str:
    parts = [
        f"{p.get('total_l')}L" if p.get("total_l") else None,
        p.get("install"),
        p.get("doors"),
        f"{p.get('energy')}등급" if p.get("energy") else None,
        material or p.get("material"),
    ]
    return " · ".join(str(part) for part in parts if part and str(part) != "-")


def _lg_price_html(value) -> str:
    try:
        if value:
            return f"{int(value):,}원"
    except Exception:
        pass
    return "가격 미정"


def _lge_product_url(code: str | None) -> str:
    safe_code = re.sub(r"[^0-9A-Za-z_-]", "", str(code or "").strip()).lower()
    return f"https://www.lge.co.kr/refrigerators/{safe_code}" if safe_code else "https://www.lge.co.kr/refrigerators"


def _color_name_parts(color_name: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"\s*/\s*", str(color_name or "")) if part.strip()]
    return parts[:2] if parts else [str(color_name or "").strip()]


def _lookup_color_hex(color_name: str) -> str:
    name = re.sub(r"\s+", " ", str(color_name or "").strip())
    if not name:
        return "#DDDDDD"
    if name in _COLOR_HEX:
        return _COLOR_HEX[name]
    for key in sorted(_COLOR_HEX, key=len, reverse=True):
        if key and key in name:
            return _COLOR_HEX[key]
    return "#DDDDDD"


def _is_light_hex(hex_color: str) -> bool:
    hex_value = str(hex_color or "").lstrip("#")
    if len(hex_value) != 6:
        return False
    try:
        r = int(hex_value[0:2], 16)
        g = int(hex_value[2:4], 16)
        b = int(hex_value[4:6], 16)
    except ValueError:
        return False
    return (r * 299 + g * 587 + b * 114) / 1000 >= 225


def _color_swatch_style(color_name: str) -> str:
    parts = _color_name_parts(color_name)
    top = _lookup_color_hex(parts[0])
    bottom = _lookup_color_hex(parts[1]) if len(parts) > 1 else top
    border = "rgba(0,0,0,0.18)" if _is_light_hex(top) or _is_light_hex(bottom) else "rgba(0,0,0,0.08)"
    if len(parts) > 1:
        background = f"linear-gradient(to bottom, {top} 0 50%, {bottom} 50% 100%)"
    else:
        background = top
    return f"background:{background};border:1px solid {border};"


def _lg_fit_label(pct: int) -> str:
    if pct >= 90:
        return "매우 적합"
    if pct >= 75:
        return "적합"
    return "비교 추천"


def _lg_feature_name(key: str) -> str:
    return SOFT_FEATURES.get(key, (key, []))[0].split(" (")[0]


def _lg_feature_tags(p: dict, ans: dict) -> str:
    lifestyle_hits = E.lifestyle_feature_set(ans) & p.get("features", set())
    if not lifestyle_hits:
        return ""
    return "".join(
        f'<span class="lg-tag lg-tag-highlight">{_html(_lg_feature_name(key))}</span>'
        for key in sorted(lifestyle_hits)
    )


def _lg_reason_tags(p: dict, ans: dict, applied_tier) -> str:
    rows = []
    install = p.get("install")
    if install:
        rows.append(f"{install} 설치")
    if applied_tier:
        rows.append(f"{E.TIER_LABEL.get(applied_tier, '')} 용량")
    elif p.get("total_l"):
        rows.append(f"총 {p.get('total_l')}L 용량")
    if p.get("energy"):
        rows.append(f"에너지 {p.get('energy')}등급")
    if p.get("doors"):
        rows.append(str(p.get("doors")))
    return "".join(f'<span class="lg-tag">{_html(text)}</span>' for text in rows if text)


def _lg_ai_text(p: dict, ans: dict, applied_tier, reason_tags: str) -> str:
    lifestyle = E.LIFESTYLE_LABELS.get(ans.get("lifestyle"), "고객")
    hit_features = sorted(E.lifestyle_feature_set(ans) & p.get("features", set()))
    feature_text = ", ".join(f"<strong>{_html(_lg_feature_name(key))}</strong>" for key in hit_features[:3])
    if not feature_text:
        feature_text = "<strong>선택 조건</strong>"
    capacity = f"{p.get('total_l')}L" if p.get("total_l") else "현재 후보군"
    energy = f"에너지 {p.get('energy')}등급" if p.get("energy") else "에너지 정보 확인 필요"
    tier_text = f"{E.TIER_LABEL.get(applied_tier)} 기준에 맞춰" if applied_tier else "선택한 조건을 기준으로"
    return (
        f"{_html(lifestyle)} 성향과 답변을 함께 보면 이 모델이 가장 안정적인 선택이에요. "
        f"{feature_text} 조건을 중심으로 잘 맞고, {_html(tier_text)} {_html(capacity)} 용량과 "
        f"<strong>{_html(energy)}</strong>을 함께 고려해 추천했어요."
    )


def _lg_check_bars(p: dict, ans: dict, applied_tier) -> str:
    breakdown = compute_breakdown(p, ans, applied_tier)
    if not breakdown:
        return ""
    rows = []
    for row in breakdown[:4]:
        score = int(row["score"])
        cls = "lg-bar-fill" if score >= 75 else "lg-bar-fill amber"
        value = round(score / 20, 1)
        rows.append(
            f'<div class="lg-bar-row">'
            f'<span class="lg-bar-label">{_html(row["label"])}</span>'
            f'<div class="lg-bar-track"><div class="{cls}" style="width:{score}%;"></div></div>'
            f'<span class="lg-bar-num">{value}</span>'
            f'</div>'
        )
    return "".join(rows)


def _lg_keyword_chips(p: dict, ans: dict) -> str:
    chips = []
    for key in sorted(p.get("features", set()))[:3]:
        chips.append(f"+ {_lg_feature_name(key)}")
    if p.get("energy") == 1:
        chips.append("+ 에너지 1등급")
    if not chips:
        chips.append("+ 기본 조건 충족")
    return "".join(f'<span class="lg-keyword">{_html(chip)}</span>' for chip in chips[:4])


def _lg_sku_html(p: dict, rank: int) -> tuple[str, str, str, int | None]:
    rep_code = p.get("code", "")
    sku = _SKU_INDEX.get(rep_code)
    variants = sku["variants"] if sku else []
    init_v = variants[0] if variants else {}
    init_code = init_v.get("code") or rep_code
    init_mat = init_v.get("material") or p.get("material", "")
    init_price = init_v.get("price") or p.get("price_min")

    if variants:
        chip_items = ""
        material_options: dict[str, dict] = {}
        for idx, v in enumerate(variants):
            cname = v.get("color", "")
            swatch_style = _color_swatch_style(cname)
            active_cls = "active" if idx == 0 else ""
            v_price = int(v.get("price") or 0)
            v_price_fmt = f"{v_price:,}원" if v_price else ""
            v_code = v.get("code") or ""
            v_mat = v.get("material") or ""
            v_spec = _lg_spec_line(p, v_mat)
            if v_mat and v_mat not in material_options:
                material_options[v_mat] = {
                    "idx": idx,
                    "code": v_code,
                    "price": v_price_fmt,
                    "mat": v_mat,
                    "url": _lge_product_url(v_code),
                    "spec": v_spec,
                }
            chip_items += (
                f'<button class="cs-chip {active_cls}"'
                f' data-rank="{rank}"'
                f' data-variant-index="{idx}"'
                f' data-code="{_html(v_code)}"'
                f' data-price="{_html(v_price_fmt)}"'
                f' data-mat="{_html(v_mat)}"'
                f' data-spec="{_html(v_spec)}"'
                f' data-url="{_html(_lge_product_url(v_code))}">'
                f'<span class="cs-dot" style="{swatch_style}"></span>'
                f'{_html(cname)}</button>'
            )
        material_select = ""
        if len(material_options) > 1:
            material_option_html = '<option value="all" selected>모두</option>'
            for mat, meta in material_options.items():
                material_option_html += (
                    f'<option value="{_html(str(meta["idx"]))}"'
                    f' data-filter-mat="{_html(mat)}"'
                    f' data-code="{_html(meta["code"])}"'
                    f' data-price="{_html(meta["price"])}"'
                    f' data-mat="{_html(meta["mat"])}"'
                    f' data-spec="{_html(meta["spec"])}"'
                    f' data-url="{_html(meta["url"])}">'
                    f'{_html(mat)}</option>'
                )
            material_select = (
                f'<select class="cs-material-select" data-rank="{rank}" aria-label="도어 재질 선택">'
                f'{material_option_html}</select>'
            )
            material_state = f'<span class="cs-info-val" id="card-mat-{rank}" style="display:none;">{_html(init_mat)}</span>'
        else:
            material_select = f'<span class="cs-info-val" id="card-mat-{rank}">{_html(init_mat)}</span>'
            material_state = ""
        html = (
            '<div class="cs-section">'
            '<div class="cs-row-label">색상 선택</div>'
            f'<div class="cs-chips">{chip_items}</div>'
            '<div class="cs-info-row">'
            '<span class="cs-info-label">도어 재질</span>'
            f'{material_select}'
            f'{material_state}'
            '</div>'
            '</div>'
        )
        return html, init_code, init_mat, int(init_price) if init_price else None

    colors = p.get("colors") or []
    if colors:
        chips = "".join(
            f'<span class="cs-chip {"active" if idx == 0 else ""}" style="cursor:default;">'
            f'<span class="cs-dot" style="{_color_swatch_style(color)}"></span>{_html(color)}</span>'
            for idx, color in enumerate(colors)
        )
        html = (
            '<div class="cs-section">'
            '<div class="cs-row-label">색상 선택</div>'
            f'<div class="cs-chips">{chips}</div>'
            '</div>'
        )
        return html, init_code, init_mat, int(init_price) if init_price else None

    return "", init_code, init_mat, int(init_price) if init_price else None


def _other_candidate_rows(scored: list[tuple[float, int, dict]]) -> str:
    if not scored:
        return ""
    rows = ""
    for fit, rank, p in scored:
        price = _lg_price_html(p.get("price_min"))
        rows += (
            '<div class="lg-candidate-row">'
            '<div style="min-width:0;">'
            f'<p class="lg-product-code">{_html(p.get("code") or "")}</p>'
            f'<p style="font-size:0.86rem;margin:1px 0;color:var(--text-primary);font-weight:700;line-height:1.35;">{_html(p.get("name") or "LG 냉장고")}</p>'
            f'<p style="font-size:0.7rem;color:var(--text-secondary);margin:0;">'
            f'{_html(str(p.get("total_l") or "—"))}L · 에너지 {_html(str(p.get("energy") or "—"))}등급 · {_html(price)}</p>'
            '</div>'
            f'<div class="lg-candidate-score">{round(fit * 100)}%</div>'
            '</div>'
        )
    return (
        '<details class="lg-other-candidates">'
        '<summary class="lg-candidates-summary">'
        f'<span>다른 추천 후보 보기 <span style="color:var(--text-tertiary);font-size:0.68rem;">{len(scored)}개</span></span>'
        '<span style="color:var(--text-tertiary);font-size:0.68rem;">▾</span>'
        '</summary>'
        f'<div class="lg-candidate-list">{rows}</div>'
        '</details>'
    )


def _compare_label(item: tuple[float, int, dict]) -> str:
    fit, rank, p = item
    code = p.get("code") or ""
    name = p.get("name") or "LG 냉장고"
    return f"TOP {rank} · {code} · {name}"


def _join_values(values) -> str:
    if values is None:
        return "-"
    if isinstance(values, set):
        values = sorted(values)
    if isinstance(values, (list, tuple)):
        cleaned = [str(v).strip() for v in values if str(v).strip() and str(v).strip() != "-"]
        return ", ".join(cleaned) if cleaned else "-"
    value = str(values).strip()
    return value if value and value != "None" else "-"


def _compare_norm(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("<br>", ", ")).strip().lower()


def _product_specs_for_compare(p: dict, fit: float) -> dict[str, str]:
    feature_names = [_lg_feature_name(key) for key in sorted(p.get("features", set()))]
    raw_features = p.get("raw_features") or []
    return {
        "제품명": _join_values(p.get("name")),
        "최저가": _lg_price_html(p.get("price_min")),
        "최고가": _lg_price_html(p.get("price_max")),
        "설치 타입": _join_values(p.get("install")),
        "도어 개수": _join_values(p.get("doors")),
        "총 용량": f"{p.get('total_l')}L" if p.get("total_l") else "-",
        "냉장 용량": f"{p.get('fridge_l')}L" if p.get("fridge_l") is not None else "-",
        "냉동 용량": f"{p.get('freezer_l')}L" if p.get("freezer_l") is not None else "-",
        "에너지 등급": f"{p.get('energy')}등급" if p.get("energy") else "-",
        "제품 크기 (너비×높이×깊이)": (
            f"{p.get('width')}×{p.get('dim_h')}×{p.get('dim_d')} mm"
            if p.get("width") and p.get("dim_h") and p.get("dim_d")
            else _join_values(p.get("size_raw")) or "-"
        ),
        "도어 재질 옵션": _join_values(p.get("materials")),
        "색상": _join_values(p.get("colors")),
        "AI 여부": "O" if p.get("is_ai") else "X",
        "매칭 기능": _join_values(feature_names),
    }


def render_top5_compare(scored: list[tuple[float, int, dict]]) -> None:
    if len(scored) < 2:
        return

    st.markdown(
        """
        <div class="lg-compare-box">
          <p class="lg-compare-title">Top 5 냉장고 서로 비교하기</p>
          <p class="lg-compare-sub">추천된 모델 중 두 가지를 선택해 저장된 스펙을 한눈에 비교해보세요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    labels = [_compare_label(item) for item in scored]
    left_col, right_col = st.columns(2)
    with left_col:
        left_idx = st.selectbox("비교 모델 A", range(len(scored)), format_func=lambda i: labels[i], key="compare_left")
    with right_col:
        default_right = 1 if len(scored) > 1 else 0
        right_idx = st.selectbox(
            "비교 모델 B",
            range(len(scored)),
            index=default_right,
            format_func=lambda i: labels[i],
            key="compare_right",
        )

    left_fit, left_rank, left_product = scored[left_idx]
    right_fit, right_rank, right_product = scored[right_idx]
    left_specs = _product_specs_for_compare(left_product, left_fit)
    right_specs = _product_specs_for_compare(right_product, right_fit)

    rows = []
    for label in left_specs:
        left_value = left_specs[label]
        right_value = right_specs.get(label, "-")
        is_diff = label != "제품명" and _compare_norm(left_value) != _compare_norm(right_value)
        diff_cls = ' class="diff-row"' if is_diff else ""
        label_html = _html(label) + ('<span class="lg-diff-badge">차이</span>' if is_diff else "")
        rows.append(
            f"<tr{diff_cls}>"
            f"<th>{label_html}</th>"
            f"<td>{left_value}</td>"
            f"<td>{right_value}</td>"
            "</tr>"
        )
    table_html = (
        '<div class="lg-compare-table-wrap">'
        '<table class="lg-compare-table">'
        '<thead><tr>'
        '<th>스펙</th>'
        f'<th>TOP {left_rank} · {_html(left_product.get("code") or "")}</th>'
        f'<th>TOP {right_rank} · {_html(right_product.get("code") or "")}</th>'
        '</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody>'
        '</table></div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)


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

# ── Q1 첫 답변 시 세션 시작 기록 (이탈 추적 기준점) ──
if "lifestyle" in ans and not st.session_state._session_start_logged:
    DB.log_session_start(st.session_state.session_id)
    st.session_state._session_start_logged = True

render_progress(q)

# ── 질문 흐름 ──
if q == "lifestyle":
    option_buttons("lifestyle")

elif q == "install":
    option_buttons("install")

elif q == "household":
    option_buttons("household")

elif q == "cooking":
    option_buttons("cooking")

elif q == "door_style":
    option_buttons("door_style")

elif q == "space":
    q_bubble(
        '<strong>설치 공간 크기를 알고 있나요?</strong>'
        '<span class="hint-block">폭·높이·깊이를 입력하면 들어가지 않는 제품을 제외해요</span>'
    )

    def _parse_cm(s):
        """cm 입력 → mm 변환 (엔진은 mm 단위 비교)"""
        if not s or not s.strip():
            return None
        try:
            val = float(s.strip().replace(",", ""))
            return int(val * 10) if val > 0 else None
        except (ValueError, TypeError):
            return None

    def _save_space(skip=False):
        _hist = st.session_state.history
        if "space" in _hist:
            idx = _hist.index("space")
            for k in _hist[idx + 1:]:
                st.session_state.answers.pop(k, None)
            st.session_state.history = _hist[:idx + 1]
        else:
            _hist.append("space")
        ans["space"] = "skip" if skip else {
            "w": _parse_cm(st.session_state.get("space_w", "")),
            "h": _parse_cm(st.session_state.get("space_h", "")),
            "d": _parse_cm(st.session_state.get("space_d", "")),
        }

    with st.container(border=True):
        col_w, col_h, col_d = st.columns(3, gap="small")
        with col_w:
            w_str = st.text_input("너비", placeholder="너비 (cm)", key="space_w",
                                  label_visibility="collapsed")
        with col_h:
            h_str = st.text_input("높이", placeholder="높이 (cm)", key="space_h",
                                  label_visibility="collapsed")
        with col_d:
            d_str = st.text_input("깊이", placeholder="깊이 (cm)", key="space_d",
                                  label_visibility="collapsed")

        bad_fields = [lbl for lbl, s in [("너비", w_str), ("높이", h_str), ("깊이", d_str)]
                      if s and s.strip() and _parse_cm(s) is None]
        if bad_fields:
            st.error(f"{', '.join(bad_fields)} 값을 숫자(cm)로 입력해주세요.")

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
            if st.button("입력 완료", type="primary", use_container_width=True, key="space_confirm"):
                st.session_state.click_count += 1
                if not bad_fields:
                    all_empty = all(
                        not s or not s.strip()
                        for s in [
                            st.session_state.get("space_w", ""),
                            st.session_state.get("space_h", ""),
                            st.session_state.get("space_d", ""),
                        ]
                    )
                    _save_space(skip=all_empty)
                    st.rerun()

        st.markdown(
            "<p style='text-align:center;color:#C0392B;font-size:0.82rem;margin-top:10px;'>"
            "모르시면 비워두고 입력 완료 버튼을 눌러주세요.</p>",
            unsafe_allow_html=True,
        )

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
        st.session_state.click_count += 1
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
        # 후보 전체에 가중치 적합도를 계산한 뒤, 점수가 가장 높은 5개만 표시합니다.
        scored_all = [
            (compute_fit_score(p, ans, tier), engine_rank + 1, p)
            for engine_rank, (_, p, _) in enumerate(ranked)
            if p and p.get("name")
        ]
        scored_all.sort(
            key=lambda item: (
                -item[0],
                item[2].get("energy") if item[2].get("energy") else 9,
                item[2].get("price_min") if item[2].get("price_min") else 10**12,
                item[1],
            )
        )
        scored = [(fit, rank + 1, p) for rank, (fit, _, p) in enumerate(scored_all[:5])]
        if not scored:
            st.markdown("""
            <div class="q-bubble" style="color:#888;">
              추천 결과로 표시할 제품 정보가 부족해요. 조건을 조금 바꿔 다시 시도해 보세요.
            </div>""", unsafe_allow_html=True)
            ranked = []
            st.stop()

        # ── DB 로그 (결과 화면 최초 진입 시 1회만) — 원본 scored 기준 ──
        if not st.session_state._db_logged:
            q_count_log = len(st.session_state.get("history", []))
            _cand_init, _ = E.filter_candidates(
                PRODUCTS, {"install": ans.get("install")} if ans.get("install") else {}
            )
            _ans_q2 = {k: ans[k] for k in ("install", "household", "cooking") if k in ans}
            _cand_q2, _ = E.filter_candidates(PRODUCTS, _ans_q2)
            _top1_p   = scored[0][2]
            _top1_fit = round(scored[0][0] * 100, 1)
            DB.log_session_result(
                session_id    = st.session_state.session_id,
                ans           = ans,
                q_count       = q_count_log,
                force_result  = st.session_state.force_result,
                click_count   = st.session_state.get("click_count", 0),
                cand_initial  = len(_cand_init),
                cand_after_q2 = len(_cand_q2),
                cand_final    = len(cand),
                top1_code     = _top1_p.get("code", ""),
                top1_fit_pct  = _top1_fit,
                dwell_sec     = time.time() - st.session_state.session_start,
            )
            st.session_state._db_logged = True

        # ── 설문 배너 (정렬 기준 위) ──────────────────────────────────────
        render_survey_banner()

        # ── 정렬 기준 선택 드롭다운 ──────────────────────────────────────
        sort_col, _ = st.columns([1, 2])
        with sort_col:
            sort_opt = st.selectbox(
                "정렬 기준",
                ["추천 순", "가격 낮은 순"],
                key="result_sort",
            )

        # 선택된 정렬 기준으로 표시용 리스트 재정렬 (Top 5 후보 자체는 변경 없음)
        if sort_opt == "가격 낮은 순":
            scored_display = sorted(
                scored,
                key=lambda item: (item[2].get("price_min") or 10**12),
            )
            scored_display = [(fit, i + 1, p) for i, (fit, _, p) in enumerate(scored_display)]
        else:
            scored_display = scored

        # 통계 박스
        q_count = len(st.session_state.get("history", []))
        db_total = len(PRODUCTS)
        cand_count = len(cand)
        render_lg_result_page(scored_display, ans, tier, cand_count, db_total)
        render_top5_compare(scored_display)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if st.button("처음부터 다시 상담", type="primary", use_container_width=True):
        reset()
        st.rerun()

# ── 하단 네비게이션 (이전 / 처음부터 / 결과 보기) — 단일 행 ──
if q != "result" and ans:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    nb, ns, nr = st.columns([1, 2, 1])
    with nb:
        if st.button("← 이전", key="go_back", use_container_width=True):
            go_back()
            st.rerun()
    with ns:
        if st.button("지금 바로 결과 보기", type="primary", key="skip_to_result", use_container_width=True):
            st.session_state.click_count += 1
            st.session_state.force_result = True
            st.rerun()
    with nr:
        if st.button("처음부터 →", key="restart_top", use_container_width=True):
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
  if (doc.getElementById('lg-interaction-handler-v6')) return;

  var code = [
    '(function(){',
    '  function applyVariant(el){',
    '    var r=el.dataset.rank;',
    '    var ce=document.getElementById("card-code-"+r);',
    '    var pe=document.getElementById("card-price-"+r);',
    '    var me=document.getElementById("card-mat-"+r);',
    '    var se=document.getElementById("card-spec-"+r);',
    '    var le=document.getElementById("card-link-"+r);',
    '    if(ce) ce.textContent=el.dataset.code||"";',
    '    if(pe) pe.textContent=el.dataset.price||"";',
    '    if(me) me.textContent=el.dataset.mat||"";',
    '    if(se && el.dataset.spec) se.textContent=el.dataset.spec;',
    '    if(le && el.dataset.url) le.href=el.dataset.url;',
    '  }',
    '  function filterMaterial(sel){',
    '    var section=sel.closest(".cs-section");',
    '    if(!section) return;',
    '    var opt=sel.options[sel.selectedIndex];',
    '    var mat=opt ? (opt.dataset.filterMat||"") : "";',
    '    var isAll=sel.value==="all";',
    '    var firstVisible=null;',
    '    section.querySelectorAll(".cs-chip[data-rank]").forEach(function(chip){',
    '      var show=isAll || chip.dataset.mat===mat;',
    '      chip.classList.toggle("is-hidden", !show);',
    '      if(show && !firstVisible) firstVisible=chip;',
    '    });',
    '    if(!isAll && firstVisible){',
    '      applyVariant(firstVisible);',
    '      section.querySelectorAll(".cs-chip[data-rank]").forEach(function(chip){ chip.classList.remove("active"); });',
    '      firstVisible.classList.add("active");',
    '    }',
    '  }',
    '  function bind(){',
    '    document.querySelectorAll(".cs-chip[data-rank]:not([data-sw])").forEach(function(c){',
    '      c.setAttribute("data-sw","1");',
    '      c.addEventListener("click",function(){',
    '        applyVariant(c);',
    '        var row=c.closest(".cs-chips");',
    '        if(row) row.querySelectorAll(".cs-chip").forEach(function(x){x.classList.remove("active");});',
    '        c.classList.add("active");',
    '      });',
    '    });',
    '    document.querySelectorAll(".cs-material-select[data-rank]:not([data-mat-bound])").forEach(function(sel){',
    '      sel.setAttribute("data-mat-bound","1");',
    '      sel.addEventListener("change",function(){',
    '        var opt=sel.options[sel.selectedIndex];',
    '        if(!opt) return;',
    '        if(sel.value==="all"){',
    '          filterMaterial(sel);',
    '          return;',
    '        }',
    '        opt.dataset.rank=sel.dataset.rank;',
    '        filterMaterial(sel);',
    '      });',
    '    });',
    '    document.querySelectorAll(".lg-carousel:not([data-lg-bound-v6])").forEach(function(root){',
    '      root.setAttribute("data-lg-bound-v6","1");',
    '      function setIndex(next){',
    '        var total=parseInt(root.dataset.total||"1",10);',
    '        var idx=Math.max(0,Math.min(total-1,next));',
    '        root.dataset.index=String(idx);',
    '        var track=root.querySelector(".lg-carousel-track");',
    '        if(track) track.style.transform="translateX("+(-idx*100)+"%)";',
    '        var cur=root.querySelector(".lg-current");',
    '        if(cur) cur.textContent=String(idx+1);',
    '        root.querySelectorAll(".lg-dot").forEach(function(dot,i){ dot.classList.toggle("active",i===idx); });',
    '        root.querySelectorAll(".lg-arrow[data-dir]").forEach(function(btn){',
    '          var dir=parseInt(btn.dataset.dir||"0",10);',
    '          var disabled=(dir<0 && idx===0) || (dir>0 && idx===total-1);',
    '          btn.disabled=disabled;',
    '          btn.classList.toggle("disabled",disabled);',
    '        });',
    '      }',
    '      root.querySelectorAll(".lg-arrow[data-dir]").forEach(function(btn){',
    '        btn.addEventListener("click",function(e){',
    '          e.preventDefault();',
    '          e.stopPropagation();',
    '          if(btn.disabled) return;',
    '          var idx=parseInt(root.dataset.index||"0",10);',
    '          var dir=parseInt(btn.dataset.dir||"0",10);',
    '          setIndex(idx+dir);',
    '        });',
    '      });',
    '      root.querySelectorAll(".lg-dot[data-index]").forEach(function(dot){',
    '        dot.addEventListener("click",function(e){',
    '          e.preventDefault();',
    '          e.stopPropagation();',
    '          setIndex(parseInt(dot.dataset.index||"0",10));',
    '        });',
    '      });',
    '      setIndex(parseInt(root.dataset.index||"0",10));',
    '    });',
    '  }',
    '  bind();',
    '  new MutationObserver(bind).observe(document.body,{childList:true,subtree:true});',
    '  setInterval(bind,400);',
    '})();'
  ].join('\\n');

  var s = doc.createElement('script');
  s.id = 'lg-interaction-handler-v6';
  s.textContent = code;
  doc.head.appendChild(s);
})();
</script>
"""

# ── 아이콘 JS 주입 (components.html → iframe → window.parent.document 접근) ──
# height=0 으로 invisible iframe, 실제 DOM 조작은 부모 프레임에서 수행
components.html(ICON_JS, height=0)
components.html(SWATCH_JS, height=0)
