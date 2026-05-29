"""어드민 페이지 — A/B 테스트 세션 데이터 조회 / CSV 저장 / 삭제."""
import os
import sys

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
.block-container { max-width: 1320px !important; padding: 2rem 2rem 4rem !important; }

.adm-header { margin-bottom: 1.8rem; border-bottom: 2px solid #E8E8E8; padding-bottom: 1rem; }
.adm-wordmark { font-size: 0.68rem; font-weight: 800; letter-spacing: 0.18em;
                color: #A50034; text-transform: uppercase; margin-bottom: 0.3rem; }
.adm-title { font-size: 1.5rem; font-weight: 800; color: #111; }
.adm-sub   { font-size: 0.82rem; color: #888; margin-top: 4px; }

/* KPI 그리드 */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(140px,1fr));
            gap: 10px; margin-bottom: 1.6rem; }
.kpi { background: #fff; border: 1.5px solid #E8E8E8; border-radius: 14px;
       padding: 16px 16px 14px; }
.kpi.accent { border-color: #FFCCD6; background: #FFF8FA; }
.kpi-num { font-size: 1.75rem; font-weight: 900; color: #111; line-height: 1; }
.kpi-num.red  { color: #A50034; }
.kpi-num.gray { color: #888; }
.kpi-label { font-size: 0.67rem; font-weight: 700; color: #AAA;
             letter-spacing: 0.07em; text-transform: uppercase; margin-top: 6px; }
.kpi-help  { font-size: 0.69rem; color: #CCC; margin-top: 2px; line-height: 1.35; }

.section-title { font-size: 0.72rem; font-weight: 800; color: #AAA;
                 letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 10px; }
</style>
"""

st.markdown(ADMIN_CSS, unsafe_allow_html=True)

# ── 헤더 ─────────────────────────────────────────────────────────────
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

# ── 별점 표시 헬퍼 ────────────────────────────────────────────────────
def _stars(score):
    if score is None:
        return "—"
    full = int(round(score))
    return "★" * full + "☆" * (5 - full) + f"  {score:.2f}"

# ── KPI 박스 ─────────────────────────────────────────────────────────
sat_display = _stars(summary["avg_satisfaction"]) if summary["avg_satisfaction"] else "—"
bounce_color = "red" if summary["bounce_rate"] > 40 else "gray"

st.markdown(f"""
<div class="kpi-grid">

  <div class="kpi accent">
    <div class="kpi-num red">{summary['total']}</div>
    <div class="kpi-label">총 세션</div>
    <div class="kpi-help">완료 {summary['completed']} · 이탈 {summary['total']-summary['completed']}</div>
  </div>

  <div class="kpi">
    <div class="kpi-num {bounce_color}">{summary['bounce_rate']}%</div>
    <div class="kpi-label">이탈률</div>
    <div class="kpi-help">결과 미도달 / 전체</div>
  </div>

  <div class="kpi">
    <div class="kpi-num">{summary['avg_click_count']}</div>
    <div class="kpi-label">평균 클릭 수</div>
    <div class="kpi-help">완료 세션 기준</div>
  </div>

  <div class="kpi">
    <div class="kpi-num">{summary['avg_dwell_sec']}s</div>
    <div class="kpi-label">평균 체류 시간</div>
    <div class="kpi-help">완료 세션 기준</div>
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
    <div class="kpi-help">(초기−최종) / 초기</div>
  </div>

  <div class="kpi">
    <div class="kpi-num">{summary['avg_bits_resolved']}</div>
    <div class="kpi-label">평균 해소 비트</div>
    <div class="kpi-help">log₂초기 − log₂최종</div>
  </div>

  <div class="kpi accent">
    <div class="kpi-num red" style="font-size:1.3rem;">{sat_display}</div>
    <div class="kpi-label">탐색 만족도</div>
    <div class="kpi-help">응답 {summary['sat_count']}건</div>
  </div>

</div>
""", unsafe_allow_html=True)

# ── 지표 설명 ─────────────────────────────────────────────────────────
with st.expander("📐 탐색 효율 지표 설명"):
    st.markdown("""
| 지표 | 계산식 | 해석 |
|------|--------|------|
| **이탈률** | 결과 미도달 세션 / 전체 세션 | 낮을수록 좋음 |
| **총 클릭 수** | 선택지 버튼 클릭 횟수 합계 | 탐색 노력 지표 |
| **체류 시간** | Q1 ~ 결과 화면 도달까지(초) | 탐색 비용 지표 |
| **필터 효율** | (초기 후보 − 최종 후보) / 초기 | 1에 가까울수록 효과적 |
| **판별 비율** | 최종 / 초기 | 낮을수록 구별력 높음 |
| **해소 비트** | log₂(초기) − log₂(최종) | 정보이론적 불확실성 감소량 |
| **탐색 만족도** | 별점 1~5 평균 | 사용자 주관적 만족 |
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

    show_cols = [
        "ts", "completed", "install", "household", "cooking", "door_style", "space",
        "wanted_features", "q_count", "click_count", "dwell_sec", "force_result",
        "cand_initial", "cand_after_q2", "cand_final",
        "top1_code", "top1_fit_pct",
        "filter_efficiency", "discrimination_ratio", "bits_resolved",
        "satisfaction_score", "satisfaction_comment",
    ]
    # 존재하는 컬럼만 선택 (마이그레이션 전 레코드 대응)
    show_cols = [c for c in show_cols if c in df.columns]
    df_view = df[show_cols].copy()
    df_view.columns = [labels.get(c, c) for c in show_cols]

    # 포맷
    if "완료 여부" in df_view.columns:
        df_view["완료 여부"] = df_view["완료 여부"].map(lambda x: "✓ 완료" if x else "✗ 이탈")
    if "필터 효율" in df_view.columns:
        df_view["필터 효율"] = df_view["필터 효율"].map(
            lambda x: f"{x:.1%}" if x is not None else "")
    if "판별 비율" in df_view.columns:
        df_view["판별 비율"] = df_view["판별 비율"].map(
            lambda x: f"{x:.3f}" if x is not None else "")
    if "해소 비트(bit)" in df_view.columns:
        df_view["해소 비트(bit)"] = df_view["해소 비트(bit)"].map(
            lambda x: f"{x:.2f}" if x is not None else "")
    if "바로결과 사용" in df_view.columns:
        df_view["바로결과 사용"] = df_view["바로결과 사용"].map(lambda x: "✓" if x else "")
    if "1위 적합도(%)" in df_view.columns:
        df_view["1위 적합도(%)"] = df_view["1위 적합도(%)"].map(
            lambda x: f"{x:.1f}%" if x is not None else "")
    if "만족도(★)" in df_view.columns:
        df_view["만족도(★)"] = df_view["만족도(★)"].map(
            lambda x: "★" * int(x) + "☆" * (5 - int(x)) if x is not None else "—")

    st.dataframe(df_view, use_container_width=True, height=500)
    st.caption(f"총 {len(df)}건 (완료 {summary['completed']}건 · 이탈 {summary['total']-summary['completed']}건) · session_id 열 제외 표시 (CSV에는 포함)")

# ── 뒤로가기 ─────────────────────────────────────────────────────────
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
if st.button("← 상담 앱으로 돌아가기"):
    st.switch_page("app.py")
