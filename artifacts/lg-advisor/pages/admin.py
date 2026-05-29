"""어드민 페이지 — A/B 테스트 세션 데이터 조회 / CSV 저장 / 삭제."""
import io
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import streamlit as st
import db

st.set_page_config(page_title="어드민 — LG 냉장고 상담", page_icon="🔧", layout="wide")

ADMIN_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
*, *::before, *::after {
  font-family: 'Pretendard', -apple-system, sans-serif !important;
  box-sizing: border-box;
}
[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }
.stApp { background: #F7F8FA !important; }
.block-container { max-width: 1280px !important; padding: 2rem 2rem 4rem !important; }

.adm-header { margin-bottom: 2rem; border-bottom: 2px solid #E8E8E8; padding-bottom: 1rem; }
.adm-wordmark { font-size: 0.68rem; font-weight: 800; letter-spacing: 0.18em;
                color: #A50034; text-transform: uppercase; margin-bottom: 0.3rem; }
.adm-title { font-size: 1.5rem; font-weight: 800; color: #111; }
.adm-sub { font-size: 0.82rem; color: #888; margin-top: 4px; }

.kpi-row { display: flex; gap: 12px; margin-bottom: 2rem; flex-wrap: wrap; }
.kpi { flex: 1; min-width: 130px; background: #fff; border: 1.5px solid #E8E8E8;
       border-radius: 14px; padding: 16px 18px; }
.kpi-num { font-size: 1.8rem; font-weight: 900; color: #111; line-height: 1; }
.kpi-num.red { color: #A50034; }
.kpi-label { font-size: 0.68rem; font-weight: 700; color: #AAA;
             letter-spacing: 0.07em; text-transform: uppercase; margin-top: 6px; }
.kpi-help { font-size: 0.7rem; color: #BBB; margin-top: 3px; line-height: 1.4; }

.section-title { font-size: 0.72rem; font-weight: 800; color: #AAA;
                 letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 10px; }
.danger-zone { background: #FFF8F8; border: 1.5px solid #FFCCD6;
               border-radius: 12px; padding: 16px 20px; margin-top: 1.5rem; }
</style>
"""

st.markdown(ADMIN_CSS, unsafe_allow_html=True)

# ── 헤더 ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="adm-header">
<div class="adm-wordmark">LG Electronics · Admin</div>
<div class="adm-title">냉장고 상담 데이터</div>
<div class="adm-sub">A/B 테스트 탐색 효율 분석 대시보드</div>
</div>
""", unsafe_allow_html=True)

# ── 데이터 로드 ───────────────────────────────────────────────────────
if "adm_refresh" not in st.session_state:
    st.session_state.adm_refresh = 0

labels  = db.col_labels()
rows    = db.fetch_all()
summary = db.fetch_summary()

# ── KPI 박스 ──────────────────────────────────────────────────────────
st.markdown(f"""
<div class="kpi-row">
<div class="kpi">
  <div class="kpi-num red">{summary['total']}</div>
  <div class="kpi-label">총 세션</div>
</div>
<div class="kpi">
  <div class="kpi-num">{summary['avg_q_count']}</div>
  <div class="kpi-label">평균 답변 질문</div>
  <div class="kpi-help">낮을수록 빠른 수렴</div>
</div>
<div class="kpi">
  <div class="kpi-num">{summary['avg_fit_pct']}%</div>
  <div class="kpi-label">평균 1위 적합도</div>
</div>
<div class="kpi">
  <div class="kpi-num">{summary['avg_filter_efficiency']}%</div>
  <div class="kpi-label">평균 필터 효율</div>
  <div class="kpi-help">(초기-최종) / 초기</div>
</div>
<div class="kpi">
  <div class="kpi-num">{summary['avg_bits_resolved']}</div>
  <div class="kpi-label">평균 해소 비트</div>
  <div class="kpi-help">log₂(초기) − log₂(최종)</div>
</div>
<div class="kpi">
  <div class="kpi-num">{summary['avg_session_sec']}s</div>
  <div class="kpi-label">평균 소요 시간</div>
</div>
</div>
""", unsafe_allow_html=True)

# ── 지표 설명 ─────────────────────────────────────────────────────────
with st.expander("📐 탐색 효율 지표 설명"):
    st.markdown("""
| 지표 | 계산식 | 의미 |
|------|--------|------|
| **필터 효율** | (초기 후보 − 최종 후보) / 초기 후보 | 1에 가까울수록 Q&A가 후보를 효과적으로 좁힘 |
| **판별 비율** | 최종 후보 / 초기 후보 | 0에 가까울수록 구별력 높음 (낮은 게 좋음) |
| **해소 비트** | log₂(초기 후보) − log₂(최종 후보) | 정보이론적 불확실성 감소량 (높은 게 좋음) |
| **답변 질문 수** | 실제 답변한 Q 수 | 적을수록 탐색 효율 좋음 |
""")

# ── 액션 버튼 ─────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>데이터 관리</div>", unsafe_allow_html=True)
col_ref, col_csv, col_del = st.columns([1, 2, 2])

with col_ref:
    if st.button("🔄 새로고침", use_container_width=True):
        st.session_state.adm_refresh += 1
        st.rerun()

with col_csv:
    if rows:
        df_export = pd.DataFrame(rows).rename(columns=labels)
        csv_bytes  = df_export.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="⬇️ CSV 저장",
            data=csv_bytes,
            file_name="lg_advisor_sessions.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.button("⬇️ CSV 저장", disabled=True, use_container_width=True)

with col_del:
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False
    if not st.session_state.confirm_delete:
        if st.button("🗑️ 전체 삭제", type="secondary", use_container_width=True):
            st.session_state.confirm_delete = True
            st.rerun()
    else:
        st.warning("정말 삭제하시겠어요? 복구할 수 없습니다.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ 확인 삭제", type="primary", use_container_width=True):
                db.delete_all()
                st.session_state.confirm_delete = False
                st.success("삭제 완료")
                st.rerun()
        with c2:
            if st.button("취소", use_container_width=True):
                st.session_state.confirm_delete = False
                st.rerun()

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── 데이터 테이블 ─────────────────────────────────────────────────────
st.markdown("<div class='section-title'>세션 로그</div>", unsafe_allow_html=True)

if not rows:
    st.info("저장된 세션이 없습니다. 상담을 진행하면 자동으로 기록됩니다.")
else:
    df = pd.DataFrame(rows)

    # 표시 컬럼 순서 및 한글 레이블
    show_cols = [
        "ts", "install", "household", "cooking", "door_style", "space",
        "wanted_features", "q_count", "force_result",
        "cand_initial", "cand_after_q2", "cand_final",
        "top1_code", "top1_fit_pct",
        "filter_efficiency", "discrimination_ratio", "bits_resolved",
        "session_sec",
    ]
    df_view = df[show_cols].copy()
    df_view.columns = [labels.get(c, c) for c in show_cols]

    # 수치 포맷
    df_view["필터 효율"]  = df_view["필터 효율"].map(lambda x: f"{x:.1%}" if x is not None else "")
    df_view["판별 비율"]  = df_view["판별 비율"].map(lambda x: f"{x:.3f}" if x is not None else "")
    df_view["해소 비트(bit)"] = df_view["해소 비트(bit)"].map(lambda x: f"{x:.2f}" if x is not None else "")
    df_view["바로결과 사용"] = df_view["바로결과 사용"].map(lambda x: "✓" if x else "")
    df_view["1위 적합도(%)"] = df_view["1위 적합도(%)"].map(lambda x: f"{x:.1f}%" if x is not None else "")

    st.dataframe(df_view, use_container_width=True, height=480)
    st.caption(f"총 {len(df)}건 · session_id 열 제외 표시 (CSV에는 포함)")

# ── 뒤로가기 ──────────────────────────────────────────────────────────
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
if st.button("← 상담 앱으로 돌아가기"):
    st.switch_page("app.py")
