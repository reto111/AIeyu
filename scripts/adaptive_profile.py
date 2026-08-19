from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
DEFAULT_USER_ID = 1
DEFAULT_USER_NAME = "本地学生"
DEFAULT_USER_EMAIL = "local-student@aieyu.local"
WINDOW_SIZE = 20
MIN_ATTEMPTS = 5


STATUS_ORDER = ["weak", "unstable", "stable", "strong"]
STATUS_ZH = {
    "weak": "薄弱",
    "unstable": "不稳定",
    "stable": "基本掌握",
    "strong": "掌握较好",
    "insufficient_data": "数据不足",
}


@dataclass
class Attempt:
    is_correct: bool
    answered_at: datetime


def parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value[:19], fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def ensure_default_user(conn: sqlite3.Connection) -> int:
    conn.execute(
        """
        INSERT OR IGNORE INTO users (id, display_name, email)
        VALUES (?, ?, ?)
        """,
        (DEFAULT_USER_ID, DEFAULT_USER_NAME, DEFAULT_USER_EMAIL),
    )
    return DEFAULT_USER_ID


def ensure_adaptive_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS question_exposures (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          question_id INTEGER NOT NULL,
          first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          seen_count INTEGER NOT NULL DEFAULT 0,
          correct_count INTEGER NOT NULL DEFAULT 0,
          wrong_count INTEGER NOT NULL DEFAULT 0,
          last_is_correct INTEGER CHECK (last_is_correct IN (0, 1)),
          last_quiz_session_id INTEGER,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id),
          FOREIGN KEY (question_id) REFERENCES questions(id),
          FOREIGN KEY (last_quiz_session_id) REFERENCES quiz_sessions(id),
          UNIQUE (user_id, question_id)
        );

        CREATE TABLE IF NOT EXISTS mastery_snapshots (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          exam_system_id INTEGER NOT NULL,
          level_id INTEGER NOT NULL,
          target_type TEXT NOT NULL CHECK (target_type IN ('question_type', 'knowledge_point')),
          target_code TEXT NOT NULL,
          target_name_zh TEXT,
          attempt_count INTEGER NOT NULL DEFAULT 0,
          wrong_count INTEGER NOT NULL DEFAULT 0,
          weighted_accuracy REAL,
          mastery_score INTEGER,
          mastery_status TEXT NOT NULL CHECK (mastery_status IN ('weak', 'unstable', 'stable', 'strong', 'insufficient_data')),
          recent_wrong_streak INTEGER NOT NULL DEFAULT 0,
          weakness_priority INTEGER NOT NULL DEFAULT 0,
          last_wrong_at TEXT,
          calculated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id),
          FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
          FOREIGN KEY (level_id) REFERENCES exam_levels(id)
        );

        CREATE TABLE IF NOT EXISTS training_recommendations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          exam_system_id INTEGER NOT NULL,
          level_id INTEGER NOT NULL,
          target_type TEXT NOT NULL CHECK (target_type IN ('question_type', 'knowledge_point')),
          target_code TEXT NOT NULL,
          target_name_zh TEXT,
          reason_code TEXT NOT NULL,
          priority INTEGER NOT NULL DEFAULT 0,
          recommended_count INTEGER NOT NULL DEFAULT 10,
          status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'used', 'dismissed')),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id),
          FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
          FOREIGN KEY (level_id) REFERENCES exam_levels(id)
        );

        CREATE INDEX IF NOT EXISTS idx_question_exposures_user_question
          ON question_exposures (user_id, question_id);
        CREATE INDEX IF NOT EXISTS idx_mastery_snapshots_user_target
          ON mastery_snapshots (user_id, exam_system_id, level_id, target_type, target_code, calculated_at);
        CREATE INDEX IF NOT EXISTS idx_training_recommendations_user_status
          ON training_recommendations (user_id, status, priority);
        """
    )


def fetch_tem8_ids(conn: sqlite3.Connection) -> tuple[int, int]:
    exam_system_id = int(conn.execute("SELECT id FROM exam_systems WHERE code = 'TEM8_RU'").fetchone()[0])
    level_id = int(
        conn.execute(
            "SELECT id FROM exam_levels WHERE exam_system_id = ? AND code = 'TEM8'",
            (exam_system_id,),
        ).fetchone()[0]
    )
    return exam_system_id, level_id


def record_question_exposure(
    conn: sqlite3.Connection,
    user_id: int,
    quiz_session_id: int,
    question_id: int,
    is_correct: bool,
    seen_at: datetime | None = None,
) -> None:
    now = (seen_at or datetime.now()).isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT INTO question_exposures (
          user_id, question_id, first_seen_at, last_seen_at, seen_count,
          correct_count, wrong_count, last_is_correct, last_quiz_session_id
        )
        VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?)
        ON CONFLICT(user_id, question_id) DO UPDATE SET
          last_seen_at = excluded.last_seen_at,
          seen_count = question_exposures.seen_count + 1,
          correct_count = question_exposures.correct_count + excluded.correct_count,
          wrong_count = question_exposures.wrong_count + excluded.wrong_count,
          last_is_correct = excluded.last_is_correct,
          last_quiz_session_id = excluded.last_quiz_session_id,
          updated_at = CURRENT_TIMESTAMP
        """,
        (
            user_id,
            question_id,
            now,
            now,
            1 if is_correct else 0,
            0 if is_correct else 1,
            1 if is_correct else 0,
            quiz_session_id,
        ),
    )


def backfill_default_user(conn: sqlite3.Connection, user_id: int = DEFAULT_USER_ID) -> None:
    conn.execute("UPDATE quiz_sessions SET user_id = ? WHERE user_id IS NULL", (user_id,))
    conn.execute("UPDATE user_answers SET user_id = ? WHERE user_id IS NULL", (user_id,))
    conn.execute("UPDATE weakness_snapshots SET user_id = ? WHERE user_id IS NULL", (user_id,))
    conn.execute("UPDATE ai_tutor_threads SET user_id = ? WHERE user_id IS NULL", (user_id,))


def rebuild_question_exposures(conn: sqlite3.Connection, user_id: int = DEFAULT_USER_ID) -> None:
    conn.execute("DELETE FROM question_exposures WHERE user_id = ?", (user_id,))
    rows = conn.execute(
        """
        SELECT qi.quiz_session_id, qi.question_id, ua.is_correct, ua.answered_at
        FROM quiz_items qi
        JOIN user_answers ua ON ua.quiz_item_id = qi.id
        JOIN quiz_sessions qs ON qs.id = qi.quiz_session_id
        WHERE COALESCE(ua.user_id, qs.user_id) = ?
        ORDER BY ua.answered_at, ua.id
        """,
        (user_id,),
    ).fetchall()
    for row in rows:
        record_question_exposure(
            conn,
            user_id,
            int(row["quiz_session_id"]),
            int(row["question_id"]),
            bool(row["is_correct"]),
            parse_datetime(row["answered_at"]),
        )


def answer_weight(answered_at: datetime, now: datetime) -> float:
    days = max((now - answered_at).total_seconds() / 86400, 0)
    if days <= 3:
        return 1.0
    if days <= 7:
        return 0.7
    if days <= 10:
        return 0.4
    return 0.2


def recent_error_weight(last_wrong_at: datetime | None, now: datetime) -> float:
    if last_wrong_at is None:
        return 0.0
    days = max((now - last_wrong_at).total_seconds() / 86400, 0)
    if days <= 3:
        return 1.0
    if days <= 7:
        return 0.7
    if days <= 10:
        return 0.4
    return 0.0


def base_status(score: int, attempt_count: int) -> str:
    if attempt_count < MIN_ATTEMPTS:
        return "insufficient_data"
    if score < 60:
        return "weak"
    if score < 75:
        return "unstable"
    if score < 88:
        return "stable"
    return "strong"


def downgrade_status(status: str, wrong_streak: int) -> str:
    if status == "insufficient_data" or wrong_streak < 2:
        return status
    index = STATUS_ORDER.index(status)
    return STATUS_ORDER[max(index - 1, 0)]


def calculate_target(
    target_type: str,
    target_code: str,
    target_name_zh: str,
    attempts: list[Attempt],
    now: datetime,
) -> dict[str, Any]:
    ordered = sorted(attempts, key=lambda item: item.answered_at, reverse=True)[:WINDOW_SIZE]
    attempt_count = len(ordered)
    wrong_count = sum(1 for item in ordered if not item.is_correct)
    weights = [answer_weight(item.answered_at, now) for item in ordered]
    total_weight = sum(weights)
    correct_weight = sum(weight for item, weight in zip(ordered, weights) if item.is_correct)
    weighted_accuracy = correct_weight / total_weight if total_weight else 0.0
    mastery_score = round(weighted_accuracy * 100)

    wrong_streak = 0
    for item in ordered:
        if item.is_correct:
            break
        wrong_streak += 1

    last_wrong_at = next((item.answered_at for item in ordered if not item.is_correct), None)
    status = downgrade_status(base_status(mastery_score, attempt_count), wrong_streak)
    error_rate = wrong_count / attempt_count if attempt_count else 0.0
    streak_weight = min(wrong_streak, 3) / 3
    priority = round(error_rate * 50 + recent_error_weight(last_wrong_at, now) * 30 + streak_weight * 20)
    if attempt_count < MIN_ATTEMPTS:
        priority = min(priority, 40)

    return {
        "target_type": target_type,
        "target_code": target_code,
        "target_name_zh": target_name_zh,
        "attempt_count": attempt_count,
        "wrong_count": wrong_count,
        "weighted_accuracy": round(weighted_accuracy, 4),
        "mastery_score": mastery_score,
        "mastery_status": status,
        "mastery_status_zh": STATUS_ZH[status],
        "recent_wrong_streak": wrong_streak,
        "weakness_priority": priority,
        "last_wrong_at": last_wrong_at.isoformat(timespec="seconds") if last_wrong_at else None,
    }


def fetch_attempt_groups(conn: sqlite3.Connection, user_id: int) -> dict[tuple[str, str, str], list[Attempt]]:
    groups: dict[tuple[str, str, str], list[Attempt]] = defaultdict(list)
    rows = conn.execute(
        """
        SELECT
          qt.code AS question_type_code,
          qt.name_zh AS question_type_name,
          kp.code AS knowledge_code,
          kp.name_zh AS knowledge_name,
          ua.is_correct,
          ua.answered_at
        FROM user_answers ua
        JOIN quiz_items qi ON qi.id = ua.quiz_item_id
        JOIN questions q ON q.id = qi.question_id
        JOIN question_types qt ON qt.id = q.question_type_id
        LEFT JOIN question_knowledge_points qkp ON qkp.question_id = q.id
        LEFT JOIN knowledge_points kp ON kp.id = qkp.knowledge_point_id
        WHERE ua.user_id = ?
        ORDER BY ua.answered_at DESC, ua.id DESC
        """,
        (user_id,),
    ).fetchall()
    for row in rows:
        attempt = Attempt(bool(row["is_correct"]), parse_datetime(row["answered_at"]))
        groups[("question_type", row["question_type_code"], row["question_type_name"])].append(attempt)
        if row["knowledge_code"]:
            groups[("knowledge_point", row["knowledge_code"], row["knowledge_name"])].append(attempt)
    return groups


def insert_mastery_snapshot(
    conn: sqlite3.Connection,
    user_id: int,
    exam_system_id: int,
    level_id: int,
    item: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO mastery_snapshots (
          user_id, exam_system_id, level_id, target_type, target_code, target_name_zh,
          attempt_count, wrong_count, weighted_accuracy, mastery_score, mastery_status,
          recent_wrong_streak, weakness_priority, last_wrong_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            exam_system_id,
            level_id,
            item["target_type"],
            item["target_code"],
            item["target_name_zh"],
            item["attempt_count"],
            item["wrong_count"],
            item["weighted_accuracy"],
            item["mastery_score"],
            item["mastery_status"],
            item["recent_wrong_streak"],
            item["weakness_priority"],
            item["last_wrong_at"],
        ),
    )


def refresh_training_recommendations(
    conn: sqlite3.Connection,
    user_id: int,
    exam_system_id: int,
    level_id: int,
    profile_items: list[dict[str, Any]],
) -> dict[str, Any] | None:
    conn.execute(
        "UPDATE training_recommendations SET status = 'used', updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND status = 'active'",
        (user_id,),
    )
    candidates = [
        item
        for item in profile_items
        if item["mastery_status"] != "insufficient_data" and item["weakness_priority"] > 0
    ]
    candidates.sort(key=lambda item: (-item["weakness_priority"], item["mastery_status"], item["target_type"]))
    if not candidates:
        return None
    top = candidates[0]
    conn.execute(
        """
        INSERT INTO training_recommendations (
          user_id, exam_system_id, level_id, target_type, target_code, target_name_zh,
          reason_code, priority, recommended_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 10)
        """,
        (
            user_id,
            exam_system_id,
            level_id,
            top["target_type"],
            top["target_code"],
            top["target_name_zh"],
            "highest_weakness_priority",
            top["weakness_priority"],
        ),
    )
    return {
        "mode": "weakness_review",
        "target_type": top["target_type"],
        "target_code": top["target_code"],
        "target_name_zh": top["target_name_zh"],
        "reason": "当前弱项优先级最高",
        "count": 10,
    }


def recalculate_profile(conn: sqlite3.Connection, user_id: int = DEFAULT_USER_ID) -> dict[str, Any]:
    ensure_adaptive_tables(conn)
    ensure_default_user(conn)
    backfill_default_user(conn, user_id)
    exam_system_id, level_id = fetch_tem8_ids(conn)
    now = datetime.now()
    groups = fetch_attempt_groups(conn, user_id)
    profile_items = [
        calculate_target(target_type, code, name, attempts, now)
        for (target_type, code, name), attempts in groups.items()
    ]
    for item in profile_items:
        insert_mastery_snapshot(conn, user_id, exam_system_id, level_id, item)
    next_training = refresh_training_recommendations(conn, user_id, exam_system_id, level_id, profile_items)
    conn.commit()
    return profile_payload(user_id, profile_items, next_training)


def profile_payload(
    user_id: int,
    profile_items: list[dict[str, Any]],
    next_training: dict[str, Any] | None,
) -> dict[str, Any]:
    question_type_mastery = [item for item in profile_items if item["target_type"] == "question_type"]
    knowledge_mastery = [item for item in profile_items if item["target_type"] == "knowledge_point"]
    top_weaknesses = sorted(
        [item for item in profile_items if item["mastery_status"] != "insufficient_data"],
        key=lambda item: -item["weakness_priority"],
    )[:3]
    return {
        "user_id": user_id,
        "exam_system": "TEM8_RU",
        "level": "TEM8",
        "question_type_mastery": question_type_mastery,
        "knowledge_mastery": knowledge_mastery,
        "top_weaknesses": top_weaknesses,
        "next_training": next_training,
    }


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
