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

    session_sec           REAL       -- 세션 시작 ~ 결과 표시까지 경과 시간(초)
)
"""

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
    "cand_initial":         "초기 후보",
    "cand_after_q2":        "Q2 후 후보",
    "cand_final":           "최종 후보",
    "top1_code":            "1위 모델",
    "top1_fit_pct":         "1위 적합도(%)",
    "filter_efficiency":    "필터 효율",
    "discrimination_ratio": "판별 비율",
    "bits_resolved":        "해소 비트(bit)",
    "session_sec":          "소요 시간(초)",
}


def _conn() -> sqlite3.Connection:
    os.makedirs(_DB_DIR, exist_ok=True)
    c = sqlite3.connect(_DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute(_CREATE_SQL)
    c.commit()
    return c


def log_session(
    ans: dict,
    q_count: int,
    force_result: bool,
    cand_initial: int,
    cand_after_q2: int,
    cand_final: int,
    top1_code: str,
    top1_fit_pct: float,
    session_sec: float,
    session_id: str | None = None,
) -> str:
    sid = session_id or str(uuid.uuid4())

    fe = (cand_initial - cand_final) / cand_initial if cand_initial > 0 else 0.0
    dr = cand_final / cand_initial if cand_initial > 0 else 1.0
    br = math.log2(max(cand_initial, 1)) - math.log2(max(cand_final, 1))

    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                sid,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ans.get("install"),
                ans.get("household"),
                ans.get("cooking"),
                ans.get("door_style"),
                ans.get("space"),
                json.dumps(ans.get("wanted_features", []), ensure_ascii=False),
                q_count,
                int(bool(force_result)),
                cand_initial,
                cand_after_q2,
                cand_final,
                top1_code,
                round(top1_fit_pct, 1),
                round(fe, 4),
                round(dr, 4),
                round(br, 4),
                round(session_sec or 0.0, 1),
            ),
        )
    return sid


def fetch_all() -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT * FROM sessions ORDER BY ts DESC").fetchall()
    return [dict(r) for r in rows]


def delete_all() -> None:
    with _conn() as c:
        c.execute("DELETE FROM sessions")


def fetch_summary() -> dict:
    with _conn() as c:
        total    = c.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        avg_fit  = c.execute("SELECT AVG(top1_fit_pct) FROM sessions").fetchone()[0]
        avg_q    = c.execute("SELECT AVG(q_count) FROM sessions").fetchone()[0]
        avg_eff  = c.execute("SELECT AVG(filter_efficiency) FROM sessions").fetchone()[0]
        avg_bits = c.execute("SELECT AVG(bits_resolved) FROM sessions").fetchone()[0]
        avg_sec  = c.execute("SELECT AVG(session_sec) FROM sessions").fetchone()[0]
    return {
        "total":                  total,
        "avg_fit_pct":            round(avg_fit  or 0, 1),
        "avg_q_count":            round(avg_q    or 0, 1),
        "avg_filter_efficiency":  round((avg_eff or 0) * 100, 1),
        "avg_bits_resolved":      round(avg_bits or 0, 2),
        "avg_session_sec":        round(avg_sec  or 0, 1),
    }


def col_labels() -> dict:
    return _COL_LABELS
