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

# ── KPI 박스 ─────────────────────────────────────────────────────────
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

</div>
""", unsafe_allow_html=True)

# ── 지표 설명 ─────────────────────────────────────────────────────────
with st.expander("📐 탐색 효율 지표 설명"):
    metric_df = pd.DataFrame({
        "지표": ["이탈률", "평균 클릭 수", "평균 체류 시간", "평균 답변 질문", "평균 1위 적합도", "필터 효율", "해소 비트"],
        "계산식": [
            "결과 미도달 세션 / 전체 세션",
            "선택지 버튼 클릭 횟수 / 완료 세션",
            "라이프스타일 선택 ~ 결과 도달까지(초)",
            "실제 답변한 질문 수 평균",
            "최상위 추천 모델 적합도 평균(%)",
            "(초기 후보 − 최종 후보) / 초기 후보",
            "log₂(초기 후보) − log₂(최종 후보)",
        ],
        "해석": [
            "낮을수록 좋음",
            "탐색 노력 지표",
            "탐색 비용 지표",
            "낮을수록 빠른 수렴",
            "높을수록 정확한 추천",
            "1에 가까울수록 효과적",
            "정보이론적 불확실성 감소량",
        ],
    })
    st.dataframe(metric_df, use_container_width=True, hide_index=True)

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
        "cand_initial", "cand_final",
        "top1_code", "top1_fit_pct",
        "filter_efficiency", "discrimination_ratio", "bits_resolved",
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

    st.dataframe(df_view, use_container_width=True, height=500)
    st.caption(f"총 {len(df)}건 (완료 {summary['completed']}건 · 이탈 {summary['total']-summary['completed']}건) · session_id 열 제외 표시 (CSV에는 포함)")

# ════════════════════════════════════════════════════════════════════
# 설문 응답 섹션
# ════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
st.markdown("""
<div style='border-top:2px solid #E8E8E8; margin-bottom:1.6rem; padding-top:1.4rem;'>
  <div class='adm-wordmark'>Survey</div>
  <div class='adm-title' style='font-size:1.2rem;'>설문 응답 분석</div>
  <div class='adm-sub'>리커트 Q1~Q8 + 주관식 Q9~Q10</div>
</div>
""", unsafe_allow_html=True)

sv_rows    = db.fetch_survey_responses()
sv_summary = db.fetch_survey_summary()

# ── 설문 KPI ─────────────────────────────────────────────────────────
_Q_LABELS = {
    "q1": "Q1 쉬운 탐색",
    "q2": "Q2 명확한 과정",
    "q3": "Q3 복잡하지 않음",
    "q4": "Q4 차이점 이해",
    "q5": "Q5 충분한 정보",
    "q6": "Q6 선택 도움",
    "q7": "Q7 제품 적합성",
    "q8": "Q8 구매 의향",
}

total_sv = sv_summary["total"]
avgs     = sv_summary["avgs"]
overall_avg = (
    round(sum(v for v in avgs.values() if v is not None)
          / max(sum(1 for v in avgs.values() if v is not None), 1), 2)
    if total_sv > 0 else None
)

sv_kpi_items = [
    (f"{total_sv}", "총 응답 수", "", "accent"),
    (
        f"{overall_avg:.2f}" if overall_avg else "—",
        "전체 평균 (Q1~Q8)",
        "1~5점 척도",
        "accent" if (overall_avg or 0) >= 3.5 else "",
    ),
]
for qk, ql in _Q_LABELS.items():
    v = avgs.get(qk)
    sv_kpi_items.append((
        f"{v:.2f}" if v is not None else "—",
        ql,
        "",
        "",
    ))

sv_kpi_html = '<div class="kpi-grid" style="grid-template-columns:repeat(auto-fit,minmax(120px,1fr));">'
for num, label, help_txt, cls in sv_kpi_items:
    color = "red" if cls == "accent" else ""
    sv_kpi_html += (
        f'<div class="kpi {cls}">'
        f'<div class="kpi-num {color}">{num}</div>'
        f'<div class="kpi-label">{label}</div>'
        + (f'<div class="kpi-help">{help_txt}</div>' if help_txt else "")
        + "</div>"
    )
sv_kpi_html += "</div>"
st.markdown(sv_kpi_html, unsafe_allow_html=True)

# ── 문항별 평균 가로 막대 차트 ─────────────────────────────────────
if total_sv > 0:
    import altair as alt  # altair는 streamlit 번들에 포함

    chart_data = pd.DataFrame([
        {"문항": lbl, "평균 점수": avgs.get(qk) or 0}
        for qk, lbl in _Q_LABELS.items()
    ])
    bar = (
        alt.Chart(chart_data)
        .mark_bar(color="#A50034", cornerRadiusEnd=4)
        .encode(
            x=alt.X("평균 점수:Q", scale=alt.Scale(domain=[1, 5]), title="평균 점수 (1~5)"),
            y=alt.Y("문항:N", sort=None, title=None),
            tooltip=["문항", alt.Tooltip("평균 점수:Q", format=".2f")],
        )
        .properties(height=240)
    )
    rule = alt.Chart(pd.DataFrame({"x": [3]})).mark_rule(
        color="#AAAAAA", strokeDash=[4, 4]
    ).encode(x="x:Q")
    st.altair_chart(bar + rule, use_container_width=True)

# ── 설문 데이터 관리 버튼 ──────────────────────────────────────────
st.markdown("<div class='section-title'>설문 데이터 관리</div>", unsafe_allow_html=True)
sv_col_csv, sv_col_del = st.columns([2, 2])

with sv_col_csv:
    if sv_rows:
        sv_df_export = pd.DataFrame(sv_rows)
        sv_csv = sv_df_export.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="⬇️ 설문 CSV 저장",
            data=sv_csv,
            file_name="lg_advisor_survey.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.button("⬇️ 설문 CSV 저장", disabled=True, use_container_width=True)

with sv_col_del:
    if "confirm_sv_delete" not in st.session_state:
        st.session_state.confirm_sv_delete = False
    if not st.session_state.confirm_sv_delete:
        if st.button("🗑️ 설문 전체 삭제", type="secondary", use_container_width=True):
            st.session_state.confirm_sv_delete = True
            st.rerun()
    else:
        st.warning("설문 응답을 모두 삭제하시겠어요? 복구 불가합니다.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ 확인 삭제", type="primary", use_container_width=True, key="sv_del_confirm"):
                db.delete_survey_responses()
                st.session_state.confirm_sv_delete = False
                st.success("삭제 완료")
                st.rerun()
        with c2:
            if st.button("취소", use_container_width=True, key="sv_del_cancel"):
                st.session_state.confirm_sv_delete = False
                st.rerun()

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ── 리커트 응답 테이블 ─────────────────────────────────────────────
st.markdown("<div class='section-title'>리커트 응답 (Q1~Q8)</div>", unsafe_allow_html=True)
if not sv_rows:
    st.info("저장된 설문 응답이 없습니다.")
else:
    sv_df = pd.DataFrame(sv_rows)
    likert_cols = ["ts", "session_id", "q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8"]
    likert_cols = [c for c in likert_cols if c in sv_df.columns]
    sv_likert = sv_df[likert_cols].copy()
    sv_likert.columns = (
        ["시각", "세션 ID"] + list(_Q_LABELS.values())
    )[:len(likert_cols)]
    st.dataframe(sv_likert, use_container_width=True, height=320)

# ── 주관식 응답 (Q9, Q10) ─────────────────────────────────────────
st.markdown("<div class='section-title' style='margin-top:16px;'>주관식 응답 (Q9~Q10)</div>", unsafe_allow_html=True)
if sv_rows:
    sv_df_open = pd.DataFrame(sv_rows)
    open_cols = ["ts", "session_id", "q9", "q10"]
    open_cols = [c for c in open_cols if c in sv_df_open.columns]
    sv_open = sv_df_open[open_cols].copy()
    sv_open.columns = (["시각", "세션 ID", "Q9 도움된 기능", "Q10 개선 의견"])[:len(open_cols)]
    # 주관식 미응답 행 (q9, q10 둘 다 None) 제외
    has_text = sv_open.iloc[:, 2:].apply(
        lambda row: row.dropna().astype(str).str.strip().str.len().sum() > 0, axis=1
    )
    sv_open_filtered = sv_open[has_text]
    if sv_open_filtered.empty:
        st.info("주관식 응답이 아직 없습니다.")
    else:
        st.dataframe(sv_open_filtered, use_container_width=True, height=300)
        st.caption(f"주관식 응답 {len(sv_open_filtered)}건 (전체 응답 {total_sv}건 중)")

# ── 뒤로가기 ─────────────────────────────────────────────────────────
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
if st.button("← 상담 앱으로 돌아가기"):
    st.switch_page("app.py")
