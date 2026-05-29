"""SQLite 세션 로그 — A/B 테스트 분류 모델 탐색 효율 측정용."""
import json
import math
import os
import sqlite3
import uuid
from datetime import datetime

_DB_DIR  = os.path.join(os.path.dirname(__file__), "data")
_DB_PATH = os.path.join(_DB_DIR, "sessions.db")

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id            TEXT PRIMARY KEY,
    ts                    TEXT NOT NULL,

    -- Q&A 답변 (입력 피처)
    install               TEXT,
    household             TEXT,
    cooking               TEXT,
    door_style            TEXT,
    space                 TEXT,
    wanted_features       TEXT,

    -- 탐색 행동 지표
    q_count               INTEGER,   -- 실제 답변한 질문 수
    force_result          INTEGER,   -- "바로 결과 보기" 사용 여부 (0/1)
    click_count           INTEGER DEFAULT 0,  -- 버튼 총 클릭 수
    dwell_sec             REAL,      -- 세션 시작~결과까지 체류 시간(초)

    -- 완료/이탈
    completed             INTEGER DEFAULT 0,  -- 결과 화면 도달 여부 (0=이탈, 1=완료)

    -- 후보 감소 흐름
    cand_initial          INTEGER,   -- install 선택 직후 후보 수
    cand_after_q2         INTEGER,   -- Q2(인원+요리) 후 후보 수
    cand_final            INTEGER,   -- 최종 후보 수

    -- 추천 결과
    top1_code             TEXT,      -- 1위 모델 코드
    top1_fit_pct          REAL,      -- 1위 종합 적합도 (%)

    -- 탐색 효율 파생 지표
    filter_efficiency     REAL,      -- (cand_initial - cand_final) / cand_initial  → 1에 가까울수록 좋음
    discrimination_ratio  REAL,      -- cand_final / cand_initial                   → 0에 가까울수록 구별력 높음
    bits_resolved         REAL,      -- log2(cand_initial) - log2(cand_final)       → 정보이론적 불확실성 감소량

    -- 만족도
    satisfaction_score    INTEGER,   -- 별점 1~5 (NULL = 미응답)
    satisfaction_comment  TEXT       -- 한 줄 의견 (선택)
)
"""

# 기존 DB 마이그레이션 — 새 컬럼이 없으면 추가
_MIGRATE_COLS = {
    "click_count":          "INTEGER DEFAULT 0",
    "dwell_sec":            "REAL",
    "completed":            "INTEGER DEFAULT 0",
    "satisfaction_score":   "INTEGER",
    "satisfaction_comment": "TEXT",
}

_COL_LABELS = {
    "session_id":           "세션 ID",
    "ts":                   "시각",
    "install":              "Q1 설치형태",
    "household":            "Q2 인원",
    "cooking":              "Q2 요리",
    "door_style":           "Q2-1 도어방식",
    "space":                "Q3 설치공간",
    "wanted_features":      "Q4 추가기능",
    "q_count":              "답변 질문 수",
    "force_result":         "바로결과 사용",
    "click_count":          "총 클릭 수",
    "dwell_sec":            "체류 시간(초)",
    "completed":            "완료 여부",
    "cand_initial":         "초기 후보",
    "cand_after_q2":        "Q2 후 후보",
    "cand_final":           "최종 후보",
    "top1_code":            "1위 모델",
    "top1_fit_pct":         "1위 적합도(%)",
    "filter_efficiency":    "필터 효율",
    "discrimination_ratio": "판별 비율",
    "bits_resolved":        "해소 비트(bit)",
    "satisfaction_score":   "만족도(★)",
    "satisfaction_comment": "한줄 의견",
}


def _conn() -> sqlite3.Connection:
    os.makedirs(_DB_DIR, exist_ok=True)
    c = sqlite3.connect(_DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute(_CREATE_SQL)
    # 마이그레이션: 신규 컬럼 추가
    existing = {row[1] for row in c.execute("PRAGMA table_info(sessions)").fetchall()}
    for col, defn in _MIGRATE_COLS.items():
        if col not in existing:
            c.execute(f"ALTER TABLE sessions ADD COLUMN {col} {defn}")
    c.commit()
    return c


# ── 세션 시작 (Q1 첫 답변 시 호출) ──────────────────────────────────
def log_session_start(session_id: str) -> None:
    """Q1(install) 답변 시점에 행을 생성 — 이탈 추적 기준점."""
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO sessions (session_id, ts, completed, click_count)"
            " VALUES (?, ?, 0, 0)",
            (session_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )


# ── 탐색 완료 (결과 화면 최초 도달 시 호출) ─────────────────────────
def log_session_result(
    session_id: str,
    ans: dict,
    q_count: int,
    force_result: bool,
    click_count: int,
    cand_initial: int,
    cand_after_q2: int,
    cand_final: int,
    top1_code: str,
    top1_fit_pct: float,
    dwell_sec: float,
) -> None:
    fe = (cand_initial - cand_final) / cand_initial if cand_initial > 0 else 0.0
    dr = cand_final / cand_initial if cand_initial > 0 else 1.0
    br = math.log2(max(cand_initial, 1)) - math.log2(max(cand_final, 1))

    with _conn() as c:
        c.execute(
            """INSERT OR REPLACE INTO sessions
               (session_id, ts,
                install, household, cooking, door_style, space, wanted_features,
                q_count, force_result, click_count, dwell_sec, completed,
                cand_initial, cand_after_q2, cand_final,
                top1_code, top1_fit_pct,
                filter_efficiency, discrimination_ratio, bits_resolved)
               VALUES (?,
                (SELECT COALESCE(ts, ?) FROM sessions WHERE session_id=?),
                ?,?,?,?,?,?,?,?,?,?,1,?,?,?,?,?,?,?,?)""",
            (
                session_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), session_id,
                ans.get("install"),
                ans.get("household"),
                ans.get("cooking"),
                ans.get("door_style"),
                ans.get("space"),
                json.dumps(ans.get("wanted_features", []), ensure_ascii=False),
                q_count,
                int(bool(force_result)),
                click_count,
                round(dwell_sec or 0.0, 1),
                cand_initial,
                cand_after_q2,
                cand_final,
                top1_code,
                round(top1_fit_pct, 1),
                round(fe, 4),
                round(dr, 4),
                round(br, 4),
            ),
        )


# ── 만족도 업데이트 (팝업 제출 시 호출) ─────────────────────────────
def log_satisfaction(session_id: str, score: int, comment: str | None = None) -> None:
    """별점(1~5)과 한 줄 의견을 기존 레코드에 업데이트."""
    with _conn() as c:
        c.execute(
            "UPDATE sessions SET satisfaction_score=?, satisfaction_comment=?"
            " WHERE session_id=?",
            (score, comment or None, session_id),
        )


# ── 조회 ─────────────────────────────────────────────────────────────
def fetch_all() -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT * FROM sessions ORDER BY ts DESC").fetchall()
    return [dict(r) for r in rows]


def delete_all() -> None:
    with _conn() as c:
        c.execute("DELETE FROM sessions")


def fetch_summary() -> dict:
    with _conn() as c:
        total      = c.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        completed  = c.execute("SELECT COUNT(*) FROM sessions WHERE completed=1").fetchone()[0]
        bounced    = total - completed
        avg_fit    = c.execute("SELECT AVG(top1_fit_pct)      FROM sessions WHERE completed=1").fetchone()[0]
        avg_q      = c.execute("SELECT AVG(q_count)           FROM sessions WHERE completed=1").fetchone()[0]
        avg_eff    = c.execute("SELECT AVG(filter_efficiency)  FROM sessions WHERE completed=1").fetchone()[0]
        avg_bits   = c.execute("SELECT AVG(bits_resolved)      FROM sessions WHERE completed=1").fetchone()[0]
        avg_dwell  = c.execute("SELECT AVG(dwell_sec)          FROM sessions WHERE completed=1").fetchone()[0]
        avg_clicks = c.execute("SELECT AVG(click_count)        FROM sessions WHERE completed=1").fetchone()[0]
        avg_sat    = c.execute("SELECT AVG(satisfaction_score) FROM sessions WHERE satisfaction_score IS NOT NULL").fetchone()[0]
        sat_count  = c.execute("SELECT COUNT(*)                FROM sessions WHERE satisfaction_score IS NOT NULL").fetchone()[0]

    return {
        "total":                 total,
        "completed":             completed,
        "bounce_rate":           round(bounced / total * 100, 1) if total > 0 else 0.0,
        "avg_fit_pct":           round(avg_fit    or 0, 1),
        "avg_q_count":           round(avg_q      or 0, 1),
        "avg_filter_efficiency": round((avg_eff   or 0) * 100, 1),
        "avg_bits_resolved":     round(avg_bits   or 0, 2),
        "avg_dwell_sec":         round(avg_dwell  or 0, 1),
        "avg_click_count":       round(avg_clicks or 0, 1),
        "avg_satisfaction":      round(avg_sat, 2) if avg_sat is not None else None,
        "sat_count":             sat_count,
    }


def col_labels() -> dict:
    return _COL_LABELS
