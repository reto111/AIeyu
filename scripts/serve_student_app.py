from __future__ import annotations

import argparse
import hashlib
import hmac
import importlib.util
import json
import mimetypes
import os
import random
import re
import secrets
import sqlite3
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timedelta
from http.cookies import SimpleCookie
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import parse_qs, urlparse

from adaptive_profile import (
    DEFAULT_USER_ID,
    ensure_adaptive_tables,
    ensure_default_user,
    parse_datetime,
    recalculate_profile,
    record_question_exposure,
)


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
STATIC_DIR = ROOT / "apps" / "student_web" / "static"
PROMPT_PATH = ROOT / "prompts" / "tutoring" / "tem8_wrong_question_tutor.md"
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_RANDOM_QUESTION_TYPES = ["grammar_choice", "literature_choice", "culture_choice"]
DIAGNOSTIC_QUESTION_TYPES = ["grammar_choice", "literature_choice", "culture_choice", "reading_choice"]
READING_QUESTION_TYPE = "reading_choice"
SESSION_COOKIE_NAME = "aieyu_session"
SESSION_DAYS = 30
PASSWORD_ITERATIONS = 210_000

WORD_REVIEW_CONFIG = {
    "unknown": {"status": "learning", "correct": 0, "wrong": 1, "days": 1, "label": "不认识"},
    "fuzzy": {"status": "fuzzy", "correct": 0, "wrong": 1, "days": 2, "label": "模糊"},
    "known": {"status": "known", "correct": 1, "wrong": 0, "days": None, "label": "认识"},
}

WORD_STATUS_NAMES = {
    "new": "未开始",
    "learning": "学习中",
    "fuzzy": "模糊",
    "known": "认识",
}

_MORPH_ANALYZER: Any = None
_MORPH_UNAVAILABLE = False


QUESTION_TYPE_NAMES = {
    "grammar_choice": "语法",
    "literature_choice": "文学",
    "culture_choice": "国情",
    "reading_choice": "阅读",
}

KNOWLEDGE_NAMES = {
    "grammar": "语法与词汇",
    "literature": "俄罗斯文学",
    "culture": "俄罗斯国情",
    "reading": "阅读理解",
}

EXPECTED_CONTENT_MINIMUMS = {
    "TEM4_RU": {"questions": 444, "words": 3000},
    "TEM8_RU": {"questions": 300, "words": 3000},
}


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        ensure_adaptive_tables(conn)
        ensure_default_user(conn)
        ensure_auth_tables(conn)
        ensure_feedback_tables(conn)
        ensure_wrongbook_tables(conn)
        ensure_daily_study_tables(conn)
        ensure_translation_tables(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def normalize_user_id(raw_value: Any) -> int:
    if raw_value in (None, ""):
        return DEFAULT_USER_ID
    user_id = int(raw_value)
    if user_id <= 0:
        raise ValueError("学生账号无效。")
    return user_id


def user_id_from_query(query: dict[str, list[str]]) -> int:
    return normalize_user_id(query.get("user_id", [DEFAULT_USER_ID])[0])


def ensure_auth_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS user_auth (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL UNIQUE,
          login_name TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_sessions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          token_hash TEXT NOT NULL UNIQUE,
          expires_at TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_user_sessions_token
          ON user_sessions (token_hash, expires_at);
        """
    )


def ensure_feedback_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS word_feedback (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          vocabulary_item_id INTEGER NOT NULL,
          feedback_text TEXT NOT NULL,
          word_snapshot TEXT,
          meaning_snapshot TEXT,
          status TEXT NOT NULL DEFAULT 'open',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY (vocabulary_item_id) REFERENCES vocabulary_items(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_word_feedback_status
          ON word_feedback (status, created_at);

        CREATE TABLE IF NOT EXISTS product_feedback (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          feedback_text TEXT NOT NULL,
          page TEXT,
          status TEXT NOT NULL DEFAULT 'open',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_product_feedback_status
          ON product_feedback (status, created_at);
        """
    )


def ensure_wrongbook_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS wrongbook_preferences (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          question_id INTEGER NOT NULL,
          note_text TEXT,
          is_favorite INTEGER NOT NULL DEFAULT 0 CHECK (is_favorite IN (0, 1)),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
          UNIQUE (user_id, question_id)
        );

        CREATE INDEX IF NOT EXISTS idx_wrongbook_preferences_user
          ON wrongbook_preferences (user_id, is_favorite, updated_at);
        """
    )


def ensure_daily_study_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS daily_study_plans (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          exam_system_id INTEGER NOT NULL,
          level_id INTEGER NOT NULL,
          plan_date TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed')),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
          FOREIGN KEY (level_id) REFERENCES exam_levels(id),
          UNIQUE (user_id, exam_system_id, level_id, plan_date)
        );

        CREATE TABLE IF NOT EXISTS daily_study_tasks (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          plan_id INTEGER NOT NULL,
          task_type TEXT NOT NULL CHECK (task_type IN ('questions', 'wrongbook', 'words')),
          sort_order INTEGER NOT NULL DEFAULT 0,
          label TEXT NOT NULL,
          target_count INTEGER NOT NULL DEFAULT 0,
          training_mode TEXT,
          target_type TEXT,
          target_code TEXT,
          target_name_zh TEXT,
          target_question_type TEXT,
          reason TEXT,
          baseline_count INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (plan_id) REFERENCES daily_study_plans(id) ON DELETE CASCADE,
          UNIQUE (plan_id, task_type)
        );

        CREATE INDEX IF NOT EXISTS idx_daily_study_plans_user_date
          ON daily_study_plans (user_id, plan_date, exam_system_id, level_id);
        CREATE INDEX IF NOT EXISTS idx_daily_study_tasks_plan
          ON daily_study_tasks (plan_id, sort_order);
        """
    )


def ensure_translation_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS selection_translation_cache (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          selected_text TEXT NOT NULL,
          context_hash TEXT NOT NULL,
          result_json TEXT NOT NULL,
          provider TEXT NOT NULL DEFAULT 'deepseek',
          hit_count INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE (selected_text, context_hash)
        );

        CREATE INDEX IF NOT EXISTS idx_selection_translation_cache_lookup
          ON selection_translation_cache (selected_text, context_hash);
        """
    )


def normalize_login_name(value: Any) -> str:
    login_name = re.sub(r"\s+", " ", str(value or "").strip())
    if not login_name:
        raise ValueError("请填写姓名。")
    if len(login_name) > 40:
        raise ValueError("姓名不要超过 40 个字符。")
    return login_name


def normalize_password(value: Any) -> str:
    password = str(value or "").strip()
    if len(password) < 8:
        raise ValueError("密码至少 8 位。")
    if len(password) > 80:
        raise ValueError("密码不要超过 80 位。")
    return password


def password_hash(password: str, salt_hex: str | None = None) -> str:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, expected_hex = stored_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
    return hmac.compare_digest(digest.hex(), expected_hex)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_cookie(token: str, max_age: int = SESSION_DAYS * 24 * 60 * 60) -> str:
    return f"{SESSION_COOKIE_NAME}={token}; Path=/; Max-Age={max_age}; HttpOnly; SameSite=Lax"


def expired_session_cookie() -> str:
    return f"{SESSION_COOKIE_NAME}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"


def create_session(conn: sqlite3.Connection, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(days=SESSION_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
        INSERT INTO user_sessions (user_id, token_hash, expires_at)
        VALUES (?, ?, ?)
        """,
        (user_id, hash_session_token(token), expires_at),
    )
    return token


def cookie_token(handler: BaseHTTPRequestHandler) -> str | None:
    raw_cookie = handler.headers.get("Cookie") or ""
    cookie = SimpleCookie()
    cookie.load(raw_cookie)
    morsel = cookie.get(SESSION_COOKIE_NAME)
    return morsel.value if morsel else None


def authenticated_user(handler: BaseHTTPRequestHandler) -> sqlite3.Row:
    token = cookie_token(handler)
    if not token:
        raise PermissionError("请先登录。")
    with db() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.display_name, u.email, u.created_at, u.updated_at
            FROM user_sessions us
            JOIN users u ON u.id = us.user_id
            WHERE us.token_hash = ?
              AND datetime(us.expires_at) > datetime('now', 'localtime')
            """,
            (hash_session_token(token),),
        ).fetchone()
        if row is None:
            raise PermissionError("登录状态已失效，请重新登录。")
        conn.execute(
            "UPDATE user_sessions SET updated_at = CURRENT_TIMESTAMP WHERE token_hash = ?",
            (hash_session_token(token),),
        )
        conn.commit()
        return row


def authenticated_user_id(handler: BaseHTTPRequestHandler) -> int:
    return int(authenticated_user(handler)["id"])


def api_auth_status(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    try:
        user = authenticated_user(handler)
    except PermissionError:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": public_user(user)}


def api_register(payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
    display_name = normalize_login_name(payload.get("display_name"))
    password = normalize_password(payload.get("password"))
    email = str(payload.get("email") or "").strip() or None
    with db() as conn:
        existing = conn.execute(
            "SELECT id FROM user_auth WHERE login_name = ?",
            (display_name,),
        ).fetchone()
        if existing:
            raise ValueError("这个姓名已经注册，请直接登录或换一个姓名。")
        cursor = conn.execute(
            """
            INSERT INTO users (display_name, email)
            VALUES (?, ?)
            """,
            (display_name, email),
        )
        user_id = int(cursor.lastrowid)
        conn.execute(
            """
            INSERT INTO user_auth (user_id, login_name, password_hash)
            VALUES (?, ?, ?)
            """,
            (user_id, display_name, password_hash(password)),
        )
        token = create_session(conn, user_id)
        conn.commit()
        user = ensure_user_exists(conn, user_id)
    return {"authenticated": True, "user": public_user(user)}, session_cookie(token)


def api_login(payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
    login_name = normalize_login_name(payload.get("display_name"))
    password = normalize_password(payload.get("password"))
    with db() as conn:
        auth = conn.execute(
            """
            SELECT ua.user_id, ua.password_hash, u.id, u.display_name, u.email, u.created_at, u.updated_at
            FROM user_auth ua
            JOIN users u ON u.id = ua.user_id
            WHERE ua.login_name = ?
            """,
            (login_name,),
        ).fetchone()
        if auth is None or not verify_password(password, auth["password_hash"]):
            raise ValueError("姓名或密码不正确。")
        token = create_session(conn, int(auth["user_id"]))
        conn.commit()
    return {"authenticated": True, "user": public_user(auth)}, session_cookie(token)


def api_logout(handler: BaseHTTPRequestHandler) -> tuple[dict[str, Any], str]:
    token = cookie_token(handler)
    if token:
        with db() as conn:
            conn.execute("DELETE FROM user_sessions WHERE token_hash = ?", (hash_session_token(token),))
            conn.commit()
    return {"authenticated": False, "user": None}, expired_session_cookie()


def ensure_user_exists(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT id, display_name, email, created_at, updated_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"没有找到学生账号 {user_id}。")
    return row


def public_user(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "display_name": row["display_name"],
        "email": row["email"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def api_users(user_id: int) -> dict[str, Any]:
    with db() as conn:
        user = ensure_user_exists(conn, user_id)
    return {"default_user_id": user_id, "users": [public_user(user)]}


def api_create_user(payload: dict[str, Any]) -> dict[str, Any]:
    display_name = normalize_login_name(payload.get("display_name"))
    email = str(payload.get("email") or "").strip() or None
    with db() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO users (display_name, email)
                VALUES (?, ?)
                """,
                (display_name, email),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("这个邮箱已经被使用。") from exc
        user_id = int(cursor.lastrowid)
        conn.commit()
        user = ensure_user_exists(conn, user_id)
    return {"user": public_user(user)}


def option_rows(conn: sqlite3.Connection, question_id: int) -> list[dict[str, str]]:
    rows = conn.execute(
        """
        SELECT option_key, option_text
        FROM question_options
        WHERE question_id = ?
        ORDER BY sort_order, option_key
        """,
        (question_id,),
    ).fetchall()
    return [{"key": row["option_key"], "text": row["option_text"]} for row in rows]


def knowledge_codes(conn: sqlite3.Connection, question_id: int) -> list[str]:
    rows = conn.execute(
        """
        SELECT kp.code
        FROM question_knowledge_points qkp
        JOIN knowledge_points kp ON kp.id = qkp.knowledge_point_id
        WHERE qkp.question_id = ?
        ORDER BY kp.sort_order, kp.code
        """,
        (question_id,),
    ).fetchall()
    return [row["code"] for row in rows]


def public_question(conn: sqlite3.Connection, row: sqlite3.Row, quiz_number: int) -> dict[str, Any]:
    source_label = row["source_label"] if row["requires_source_label"] else None
    return {
        "quiz_number": quiz_number,
        "question_id": row["id"],
        "question_type": row["question_type"],
        "question_type_name": QUESTION_TYPE_NAMES.get(row["question_type"], row["question_type"]),
        "stem": row["stem"],
        "options": option_rows(conn, int(row["id"])),
        "source": {
            "year": row["source_year"],
            "question_number": row["source_question_number"],
            "label": source_label,
            "content_origin": row["content_origin"],
        },
        "knowledge_point_codes": knowledge_codes(conn, int(row["id"])),
        "passage": {
            "id": row["passage_id"],
            "title": row["passage_title"],
            "body": row["passage_body"],
        }
        if row["passage_id"]
        else None,
    }


def fetch_question(conn: sqlite3.Connection, question_id: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT
          q.id,
          q.exam_system_id,
          q.level_id,
          q.source_year,
          q.source_question_number,
          q.source_label,
          q.requires_source_label,
          q.content_origin,
          q.stem,
          q.correct_answer,
          qt.code AS question_type,
          p.id AS passage_id,
          p.title AS passage_title,
          p.body AS passage_body
        FROM questions q
        JOIN question_types qt ON qt.id = q.question_type_id
        LEFT JOIN passages p ON p.id = q.passage_id
        WHERE q.id = ?
          AND q.review_status = 'approved'
          AND q.source_usage = 'practice'
        """,
        (question_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Question {question_id} is not available.")
    return row


def api_status(exam_system_code: str = "TEM8_RU", level_code: str = "TEM8") -> dict[str, Any]:
    with db() as conn:
        exam_system_id, level_id = fetch_ids(conn, exam_system_code, level_code)
        by_type = [{"code": row["code"], "name": QUESTION_TYPE_NAMES.get(row["code"], row["name_zh"]), "count": row["count"]} for row in conn.execute("""
            SELECT qt.code, qt.name_zh, COUNT(*) AS count
            FROM questions q JOIN question_types qt ON qt.id = q.question_type_id
            WHERE q.review_status = 'approved' AND q.source_usage = 'practice'
              AND q.exam_system_id = ? AND q.level_id = ?
            GROUP BY qt.code, qt.name_zh ORDER BY qt.code
        """, (exam_system_id, level_id)).fetchall()]
        years = [{"year": row["source_year"], "count": row["count"]} for row in conn.execute("""
            SELECT source_year, COUNT(*) AS count FROM questions
            WHERE review_status = 'approved' AND source_usage = 'practice'
              AND exam_system_id = ? AND level_id = ?
            GROUP BY source_year ORDER BY source_year
        """, (exam_system_id, level_id)).fetchall()]
        latest_thread = conn.execute("SELECT id, quiz_session_id, title, updated_at FROM ai_tutor_threads ORDER BY id DESC LIMIT 1").fetchone()
    return {"exam_system": exam_system_code, "level": level_code, "question_count": sum(item["count"] for item in by_type), "question_types": by_type, "years": years, "latest_thread": dict(latest_thread) if latest_thread else None, "deepseek_configured": bool(os.environ.get("DEEPSEEK_API_KEY"))}


def api_health() -> dict[str, Any]:
    required_tables = {
        "users",
        "user_auth",
        "questions",
        "question_options",
        "passages",
        "vocabulary_items",
        "quiz_sessions",
        "user_answers",
        "question_exposures",
        "mastery_snapshots",
        "daily_study_plans",
        "wrongbook_preferences",
        "selection_translation_cache",
    }
    checks: list[dict[str, Any]] = []
    pools: dict[str, dict[str, int]] = {}
    try:
        with db() as conn:
            integrity = str(conn.execute("PRAGMA quick_check").fetchone()[0])
            checks.append({"code": "database_integrity", "ok": integrity == "ok", "detail": integrity})
            available_tables = {
                str(row[0])
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
            }
            missing_tables = sorted(required_tables - available_tables)
            checks.append(
                {
                    "code": "required_tables",
                    "ok": not missing_tables,
                    "detail": "ok" if not missing_tables else "缺少: " + ", ".join(missing_tables),
                }
            )
            for exam_code, level_code in (("TEM4_RU", "TEM4"), ("TEM8_RU", "TEM8")):
                exam_system_id, level_id = fetch_ids(conn, exam_code, level_code)
                question_count = int(
                    conn.execute(
                        """
                        SELECT COUNT(*) FROM questions
                        WHERE exam_system_id = ? AND level_id = ?
                          AND review_status = 'approved' AND source_usage = 'practice'
                        """,
                        (exam_system_id, level_id),
                    ).fetchone()[0]
                )
                word_count = int(
                    conn.execute(
                        """
                        SELECT COUNT(*) FROM vocabulary_items
                        WHERE exam_system_id = ? AND level_id = ? AND review_status = 'approved'
                        """,
                        (exam_system_id, level_id),
                    ).fetchone()[0]
                )
                pools[exam_code] = {"questions": question_count, "words": word_count}
                minimum = EXPECTED_CONTENT_MINIMUMS[exam_code]
                checks.append(
                    {
                        "code": f"{exam_code.lower()}_content_pool",
                        "ok": question_count >= minimum["questions"] and word_count >= minimum["words"],
                        "detail": (
                            f"{question_count} 题 / {word_count} 词；"
                            f"最低 {minimum['questions']} 题 / {minimum['words']} 词"
                        ),
                    }
                )
    except Exception as exc:
        checks.append({"code": "database_access", "ok": False, "detail": str(exc)})

    static_missing = [name for name in ("index.html", "app.js", "styles.css") if not (STATIC_DIR / name).exists()]
    checks.append(
        {
            "code": "student_web_files",
            "ok": not static_missing,
            "detail": "ok" if not static_missing else "缺少: " + ", ".join(static_missing),
        }
    )
    deepseek_configured = bool(os.environ.get("DEEPSEEK_API_KEY"))
    morphology_available = importlib.util.find_spec("pymorphy3") is not None
    checks.append(
        {
            "code": "deepseek_configuration",
            "ok": deepseek_configured,
            "detail": "已配置" if deepseek_configured else "未配置",
        }
    )
    checks.append(
        {
            "code": "russian_morphology",
            "ok": morphology_available,
            "detail": "pymorphy3 可用" if morphology_available else "请安装 requirements-web.txt",
        }
    )
    ready = all(bool(item["ok"]) for item in checks)
    return {
        "status": "ok" if ready else "degraded",
        "ready": ready,
        "service": "AIeyu student app",
        "checks": checks,
        "content_pools": pools,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
    }

def clean_word_meaning_for_display(value: str | None) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    text = re.sub(r"^[^\u4e00-\u9fff]*(?:未|完)[；;，,\s、-]*", "", text)
    text = re.sub(r"^[‚,，;；、\-\s()（）《》【】\\[\\]]+", "", text)
    text = text.replace("...", "某物")
    text = text.replace("…", "某物")
    text = re.sub(r"\s+", " ", text).strip(" ;；,，、")
    return text


def public_word(row: sqlite3.Row) -> dict[str, Any]:
    row_keys = set(row.keys())
    examples_raw = row["examples"] if "examples" in row_keys else ""
    examples = [
        clean_word_meaning_for_display(item)
        for item in str(examples_raw or "").split("\n")
        if clean_word_meaning_for_display(item)
    ][:3]
    return {
        "vocabulary_item_id": row["id"],
        "word": row["word"],
        "lemma": row["lemma"],
        "part_of_speech": row["part_of_speech"],
        "meaning_zh": clean_word_meaning_for_display(row["meaning_zh"]),
        "examples": examples,
        "source_page": row["source_page"],
        "progress_status": row["progress_status"] or "new",
        "progress_status_zh": WORD_STATUS_NAMES.get(row["progress_status"] or "new", "未开始"),
        "seen_count": row["seen_count"] or 0,
        "correct_count": row["correct_count"] or 0,
        "wrong_count": row["wrong_count"] or 0,
        "next_review_at": row["next_review_at"],
    }


def api_word_status(
    user_id: int = DEFAULT_USER_ID,
    exam_system_code: str = "TEM8_RU",
    level_code: str = "TEM8",
) -> dict[str, Any]:
    with db() as conn:
        user = ensure_user_exists(conn, user_id)
        exam_system_id, level_id = fetch_ids(conn, exam_system_code, level_code)
        total = conn.execute(
            """
            SELECT COUNT(*) FROM vocabulary_items
            WHERE review_status = 'approved' AND exam_system_id = ? AND level_id = ?
            """,
            (exam_system_id, level_id),
        ).fetchone()[0]
        progress_total = conn.execute(
            """
            SELECT COUNT(*) FROM user_word_progress uwp
            JOIN vocabulary_items vi ON vi.id = uwp.vocabulary_item_id
            WHERE uwp.user_id = ? AND vi.exam_system_id = ? AND vi.level_id = ?
            """,
            (user_id, exam_system_id, level_id),
        ).fetchone()[0]
        reviewed_today = conn.execute(
            """
            SELECT COUNT(DISTINCT wrl.vocabulary_item_id)
            FROM word_review_logs wrl
            JOIN vocabulary_items vi ON vi.id = wrl.vocabulary_item_id
            WHERE wrl.user_id = ?
              AND vi.exam_system_id = ? AND vi.level_id = ?
              AND date(wrl.reviewed_at) = date('now', 'localtime')
            """,
            (user_id, exam_system_id, level_id),
        ).fetchone()[0]
        due_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM user_word_progress uwp
            JOIN vocabulary_items vi ON vi.id = uwp.vocabulary_item_id
            WHERE uwp.user_id = ?
              AND vi.exam_system_id = ? AND vi.level_id = ?
              AND uwp.next_review_at IS NOT NULL
              AND datetime(uwp.next_review_at) <= datetime('now', 'localtime')
            """,
            (user_id, exam_system_id, level_id),
        ).fetchone()[0]
        review_pool_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM user_word_progress uwp
            JOIN vocabulary_items vi ON vi.id = uwp.vocabulary_item_id
            WHERE uwp.user_id = ?
              AND vi.exam_system_id = ? AND vi.level_id = ?
              AND uwp.status IN ('learning', 'fuzzy')
              AND uwp.next_review_at IS NOT NULL
            """,
            (user_id, exam_system_id, level_id),
        ).fetchone()[0]
        by_status = {
            row["status"]: row["count"]
            for row in conn.execute(
                """
                SELECT uwp.status, COUNT(*) AS count
                FROM user_word_progress uwp
                JOIN vocabulary_items vi ON vi.id = uwp.vocabulary_item_id
                WHERE uwp.user_id = ?
                  AND vi.exam_system_id = ? AND vi.level_id = ?
                GROUP BY uwp.status
                """,
                (user_id, exam_system_id, level_id),
            ).fetchall()
        }
    return {
        "user": public_user(user),
        "total_words": total,
        "new_count": max(total - progress_total, 0),
        "progress_total": progress_total,
        "reviewed_today": reviewed_today,
        "due_count": due_count,
        "review_pool_count": review_pool_count,
        "by_status": [
            {
                "status": status,
                "name_zh": WORD_STATUS_NAMES[status],
                "count": int(by_status.get(status, 0)),
            }
            for status in ["learning", "fuzzy", "known"]
        ],
    }


def select_review_pool_rows(
    conn: sqlite3.Connection,
    user_id: int,
    count: int,
    exam_system_id: int,
    level_id: int,
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          vi.id, vi.word, vi.lemma, vi.part_of_speech, vi.meaning_zh, vi.source_page,
          uwp.status AS progress_status, uwp.seen_count, uwp.correct_count, uwp.wrong_count,
          uwp.next_review_at,
          (
            SELECT group_concat(vf.form_text, char(10))
            FROM vocabulary_forms vf
            WHERE vf.vocabulary_item_id = vi.id AND vf.form_type = 'example'
          ) AS examples
        FROM user_word_progress uwp
        JOIN vocabulary_items vi ON vi.id = uwp.vocabulary_item_id
        WHERE uwp.user_id = ?
          AND vi.review_status = 'approved'
          AND vi.exam_system_id = ? AND vi.level_id = ?
          AND uwp.status IN ('learning', 'fuzzy')
          AND uwp.next_review_at IS NOT NULL
        ORDER BY
          CASE WHEN datetime(uwp.next_review_at) <= datetime('now', 'localtime') THEN 0 ELSE 1 END,
          datetime(uwp.next_review_at),
          uwp.wrong_count DESC,
          RANDOM()
        LIMIT ?
        """,
        (user_id, exam_system_id, level_id, count),
    ).fetchall()


def api_word_review_pool(
    user_id: int = DEFAULT_USER_ID,
    limit: int = 80,
    exam_system_code: str = "TEM8_RU",
    level_code: str = "TEM8",
) -> dict[str, Any]:
    limit = max(1, min(int(limit or 80), 200))
    with db() as conn:
        user = ensure_user_exists(conn, user_id)
        exam_system_id, level_id = fetch_ids(conn, exam_system_code, level_code)
        total = conn.execute(
            """
            SELECT COUNT(*)
            FROM user_word_progress uwp
            JOIN vocabulary_items vi ON vi.id = uwp.vocabulary_item_id
            WHERE uwp.user_id = ?
              AND vi.exam_system_id = ? AND vi.level_id = ?
              AND uwp.status IN ('learning', 'fuzzy')
              AND uwp.next_review_at IS NOT NULL
            """,
            (user_id, exam_system_id, level_id),
        ).fetchone()[0]
        due_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM user_word_progress uwp
            JOIN vocabulary_items vi ON vi.id = uwp.vocabulary_item_id
            WHERE uwp.user_id = ?
              AND vi.exam_system_id = ? AND vi.level_id = ?
              AND uwp.status IN ('learning', 'fuzzy')
              AND uwp.next_review_at IS NOT NULL
              AND datetime(uwp.next_review_at) <= datetime('now', 'localtime')
            """,
            (user_id, exam_system_id, level_id),
        ).fetchone()[0]
        rows = select_review_pool_rows(conn, user_id, limit, exam_system_id, level_id)
        words = [public_word(row) for row in rows]
    return {
        "user": public_user(user),
        "total": total,
        "due_count": due_count,
        "words": words,
    }


def select_word_rows(
    conn: sqlite3.Connection,
    user_id: int,
    count: int,
    exam_system_id: int,
    level_id: int,
) -> list[sqlite3.Row]:
    selected: list[sqlite3.Row] = []
    due_rows = conn.execute(
        """
        SELECT
          vi.id, vi.word, vi.lemma, vi.part_of_speech, vi.meaning_zh, vi.source_page,
          uwp.status AS progress_status, uwp.seen_count, uwp.correct_count, uwp.wrong_count,
          uwp.next_review_at,
          (
            SELECT group_concat(vf.form_text, char(10))
            FROM vocabulary_forms vf
            WHERE vf.vocabulary_item_id = vi.id AND vf.form_type = 'example'
          ) AS examples
        FROM user_word_progress uwp
        JOIN vocabulary_items vi ON vi.id = uwp.vocabulary_item_id
        WHERE uwp.user_id = ?
          AND vi.review_status = 'approved'
          AND vi.exam_system_id = ? AND vi.level_id = ?
          AND uwp.next_review_at IS NOT NULL
          AND datetime(uwp.next_review_at) <= datetime('now', 'localtime')
          AND NOT EXISTS (
            SELECT 1
            FROM word_review_logs wrl
            WHERE wrl.user_id = uwp.user_id
              AND wrl.vocabulary_item_id = uwp.vocabulary_item_id
              AND date(wrl.reviewed_at) = date('now', 'localtime')
          )
        ORDER BY datetime(uwp.next_review_at), uwp.wrong_count DESC, RANDOM()
        LIMIT ?
        """,
        (user_id, exam_system_id, level_id, count),
    ).fetchall()
    selected.extend(due_rows)

    remaining = count - len(selected)
    if remaining <= 0:
        return selected
    selected_ids = [int(row["id"]) for row in selected]
    selected_filter = ""
    params: list[Any] = [user_id, exam_system_id, level_id]
    if selected_ids:
        selected_filter = f"AND vi.id NOT IN ({', '.join('?' for _ in selected_ids)})"
        params.extend(selected_ids)
    params.append(remaining)
    new_rows = conn.execute(
        f"""
        SELECT
          vi.id, vi.word, vi.lemma, vi.part_of_speech, vi.meaning_zh, vi.source_page,
          NULL AS progress_status, 0 AS seen_count, 0 AS correct_count, 0 AS wrong_count,
          NULL AS next_review_at,
          (
            SELECT group_concat(vf.form_text, char(10))
            FROM vocabulary_forms vf
            WHERE vf.vocabulary_item_id = vi.id AND vf.form_type = 'example'
          ) AS examples
        FROM vocabulary_items vi
        LEFT JOIN user_word_progress uwp
          ON uwp.vocabulary_item_id = vi.id AND uwp.user_id = ?
        WHERE vi.review_status = 'approved'
          AND vi.exam_system_id = ? AND vi.level_id = ?
          AND uwp.id IS NULL
          {selected_filter}
        ORDER BY
          CASE WHEN vi.frequency_rank IS NULL THEN 1 ELSE 0 END,
          vi.frequency_rank,
          RANDOM()
        LIMIT ?
        """,
        params,
    ).fetchall()
    selected.extend(new_rows)
    return selected


def api_word_session(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = normalize_user_id(payload.get("user_id"))
    count = max(1, min(int(payload.get("count") or 20), 50))
    mode = str(payload.get("mode") or "mixed").strip()
    exam_system_code = str(payload.get("exam_system") or "TEM8_RU")
    level_code = str(payload.get("level") or "TEM8")
    with db() as conn:
        user = ensure_user_exists(conn, user_id)
        exam_system_id, level_id = fetch_ids(conn, exam_system_code, level_code)
        rows = (
            select_review_pool_rows(conn, user_id, count, exam_system_id, level_id)
            if mode == "review"
            else select_word_rows(conn, user_id, count, exam_system_id, level_id)
        )
        user_payload = public_user(user)
        words = [public_word(row) for row in rows]
    status = api_word_status(user_id, exam_system_code, level_code)
    return {
        "user": user_payload,
        "count": len(words),
        "mode": "review" if mode == "review" else "mixed",
        "words": words,
        "status": status,
    }


def next_word_review_time(result: str) -> str:
    days = WORD_REVIEW_CONFIG[result]["days"]
    if days is None:
        return ""
    days = int(days)
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")


def api_word_review(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = normalize_user_id(payload.get("user_id"))
    vocabulary_item_id = int(payload.get("vocabulary_item_id") or 0)
    result = str(payload.get("result") or "").strip()
    previous_result = str(payload.get("previous_result") or "").strip()
    is_correction = bool(payload.get("correction"))
    exam_system_code = str(payload.get("exam_system") or "TEM8_RU")
    level_code = str(payload.get("level") or "TEM8")
    if result not in WORD_REVIEW_CONFIG:
        raise ValueError("请选择：不认识、模糊或认识。")
    if previous_result and previous_result not in WORD_REVIEW_CONFIG:
        previous_result = ""

    config = WORD_REVIEW_CONFIG[result]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    next_review_at = next_word_review_time(result) or None

    with db() as conn:
        ensure_user_exists(conn, user_id)
        exam_system_id, level_id = fetch_ids(conn, exam_system_code, level_code)
        word = conn.execute(
            """
            SELECT
              id, word, lemma, part_of_speech, meaning_zh, source_page,
              NULL AS progress_status, 0 AS seen_count, 0 AS correct_count,
              0 AS wrong_count, NULL AS next_review_at
            FROM vocabulary_items
            WHERE id = ?
              AND review_status = 'approved'
              AND exam_system_id = ? AND level_id = ?
            """,
            (vocabulary_item_id, exam_system_id, level_id),
        ).fetchone()
        if word is None:
            raise ValueError("没有找到这个已审核单词。")

        current = conn.execute(
            """
            SELECT seen_count, correct_count, wrong_count, ease_factor
            FROM user_word_progress
            WHERE user_id = ? AND vocabulary_item_id = ?
            """,
            (user_id, vocabulary_item_id),
        ).fetchone()
        seen_delta = 0 if is_correction and current else 1
        previous_config = WORD_REVIEW_CONFIG.get(previous_result) if is_correction else None
        correct_delta = int(config["correct"]) - int(previous_config["correct"]) if previous_config else int(config["correct"])
        wrong_delta = int(config["wrong"]) - int(previous_config["wrong"]) if previous_config else int(config["wrong"])
        seen_count = int(current["seen_count"] if current else 0) + seen_delta
        correct_count = max(0, int(current["correct_count"] if current else 0) + correct_delta)
        wrong_count = max(0, int(current["wrong_count"] if current else 0) + wrong_delta)
        ease_factor = float(current["ease_factor"] if current else 2.5)
        if result == "unknown":
            ease_factor = max(1.3, ease_factor - 0.2)
        elif result == "fuzzy":
            ease_factor = max(1.3, ease_factor - 0.1)
        elif result == "known":
            ease_factor = min(3.0, ease_factor + 0.05)

        conn.execute(
            """
            INSERT INTO user_word_progress (
              user_id, vocabulary_item_id, status, seen_count, correct_count,
              wrong_count, last_seen_at, next_review_at, ease_factor, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, vocabulary_item_id) DO UPDATE SET
              status = excluded.status,
              seen_count = excluded.seen_count,
              correct_count = excluded.correct_count,
              wrong_count = excluded.wrong_count,
              last_seen_at = excluded.last_seen_at,
              next_review_at = excluded.next_review_at,
              ease_factor = excluded.ease_factor,
              updated_at = excluded.updated_at
            """,
            (
                user_id,
                vocabulary_item_id,
                config["status"],
                seen_count,
                correct_count,
                wrong_count,
                now,
                next_review_at,
                ease_factor,
                now,
            ),
        )
        conn.execute(
            """
            INSERT INTO word_review_logs (
              user_id, vocabulary_item_id, review_mode, prompt_type, user_response, result, reviewed_at
            )
            VALUES (?, ?, ?, 'ru_to_zh', ?, ?, ?)
            """,
            (
                user_id,
                vocabulary_item_id,
                "daily_checkin",
                f"{config['label']}（校正）" if is_correction else config["label"],
                result,
                now,
            ),
        )
        conn.commit()
        updated = conn.execute(
            """
            SELECT
              vi.id, vi.word, vi.lemma, vi.part_of_speech, vi.meaning_zh, vi.source_page,
              uwp.status AS progress_status, uwp.seen_count, uwp.correct_count,
              uwp.wrong_count, uwp.next_review_at,
              (
                SELECT group_concat(vf.form_text, char(10))
                FROM vocabulary_forms vf
                WHERE vf.vocabulary_item_id = vi.id AND vf.form_type = 'example'
              ) AS examples
            FROM vocabulary_items vi
            JOIN user_word_progress uwp ON uwp.vocabulary_item_id = vi.id
            WHERE vi.id = ? AND uwp.user_id = ?
            """,
            (vocabulary_item_id, user_id),
        ).fetchone()
        word_payload = public_word(updated)
    status = api_word_status(user_id, exam_system_code, level_code)
    return {"word": word_payload, "status": status, "next_review_at": next_review_at}


def clean_feedback_text(value: Any, field_name: str = "反馈内容") -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if not text:
        raise ValueError(f"请填写{field_name}。")
    if len(text) > 1000:
        raise ValueError(f"{field_name}请控制在 1000 字以内。")
    return text


def api_word_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = normalize_user_id(payload.get("user_id"))
    vocabulary_item_id = int(payload.get("vocabulary_item_id") or 0)
    feedback_text = clean_feedback_text(payload.get("feedback_text"), "单词问题")
    with db() as conn:
        ensure_user_exists(conn, user_id)
        word = conn.execute(
            """
            SELECT id, word, meaning_zh
            FROM vocabulary_items
            WHERE id = ? AND review_status = 'approved'
            """,
            (vocabulary_item_id,),
        ).fetchone()
        if not word:
            raise ValueError("没有找到这个单词。")
        cursor = conn.execute(
            """
            INSERT INTO word_feedback (
              user_id, vocabulary_item_id, feedback_text, word_snapshot, meaning_snapshot
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, vocabulary_item_id, feedback_text, word["word"], word["meaning_zh"]),
        )
        conn.commit()
    return {"status": "ok", "feedback_id": cursor.lastrowid}


def api_product_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = normalize_user_id(payload.get("user_id"))
    feedback_text = clean_feedback_text(payload.get("feedback_text"), "建议")
    page = re.sub(r"\s+", " ", str(payload.get("page") or "").strip())[:80]
    with db() as conn:
        ensure_user_exists(conn, user_id)
        cursor = conn.execute(
            """
            INSERT INTO product_feedback (user_id, feedback_text, page)
            VALUES (?, ?, ?)
            """,
            (user_id, feedback_text, page),
        )
        conn.commit()
    return {"status": "ok", "feedback_id": cursor.lastrowid}


def exposure_rows(conn: sqlite3.Connection, user_id: int, question_ids: list[int]) -> dict[int, sqlite3.Row]:
    if not question_ids:
        return {}
    placeholders = ", ".join("?" for _ in question_ids)
    rows = conn.execute(
        f"""
        SELECT question_id, seen_count, correct_count, wrong_count, last_is_correct, last_seen_at
        FROM question_exposures
        WHERE user_id = ? AND question_id IN ({placeholders})
        """,
        [user_id, *question_ids],
    ).fetchall()
    return {int(row["question_id"]): row for row in rows}


def adaptive_selection_score(exposure: sqlite3.Row | None, rng: random.Random) -> float:
    if exposure is None:
        return 100 + rng.random()
    seen_count = int(exposure["seen_count"] or 0)
    correct_count = int(exposure["correct_count"] or 0)
    wrong_count = int(exposure["wrong_count"] or 0)
    total = max(correct_count + wrong_count, 1)
    error_rate = wrong_count / total
    days_since_last_seen = 30
    if exposure["last_seen_at"]:
        days_since_last_seen = min((datetime.now() - parse_datetime(exposure["last_seen_at"])).days, 30)
    score = rng.random()
    if exposure["last_is_correct"] == 0:
        score += 40
    score += error_rate * 30
    score += days_since_last_seen
    if exposure["last_is_correct"] == 1 and days_since_last_seen < 7:
        score -= 50
    score -= seen_count * 5
    return score


def source_question_number(row: sqlite3.Row) -> int:
    try:
        return int(row["source_question_number"])
    except (TypeError, ValueError):
        return 0


def question_unit_score(
    unit: list[sqlite3.Row],
    exposures: dict[int, sqlite3.Row],
    rng: random.Random,
) -> float:
    if not unit:
        return 0
    scores = [
        adaptive_selection_score(exposures.get(int(row["id"])), rng)
        for row in unit
    ]
    return sum(scores) / len(scores)


def complete_question_units(rows: list[sqlite3.Row]) -> list[list[sqlite3.Row]]:
    units: list[list[sqlite3.Row]] = []
    reading_groups: dict[int, list[sqlite3.Row]] = {}

    for row in rows:
        if row["question_type"] == READING_QUESTION_TYPE and row["passage_id"]:
            reading_groups.setdefault(int(row["passage_id"]), []).append(row)
        else:
            units.append([row])

    for group in reading_groups.values():
        units.append(sorted(group, key=source_question_number))

    return units


def select_complete_units(
    rows: list[sqlite3.Row],
    target_count: int,
    exposures: dict[int, sqlite3.Row],
    rng: random.Random,
) -> list[sqlite3.Row]:
    if target_count <= 0:
        return []

    selected: list[sqlite3.Row] = []
    units = sorted(
        complete_question_units(rows),
        key=lambda unit: question_unit_score(unit, exposures, rng),
        reverse=True,
    )
    for unit in units:
        selected.extend(unit)
        if len(selected) >= target_count:
            break
    return selected


def select_balanced_by_type(
    rows: list[sqlite3.Row],
    count: int,
    question_types: list[str],
    exposures: dict[int, sqlite3.Row],
    rng: random.Random,
) -> list[sqlite3.Row]:
    grouped: dict[str, list[sqlite3.Row]] = {code: [] for code in question_types}
    for row in rows:
        grouped.setdefault(row["question_type"], []).append(row)

    selected: list[sqlite3.Row] = []
    remaining_pool: list[sqlite3.Row] = []
    base = count // max(len(question_types), 1)
    remainder = count % max(len(question_types), 1)

    for index, code in enumerate(question_types):
        target = base + (1 if index < remainder else 0)
        candidates = grouped.get(code, [])
        if code == READING_QUESTION_TYPE:
            picked = select_complete_units(candidates, target, exposures, rng)
            picked_ids = {int(row["id"]) for row in picked}
            selected.extend(picked)
            remaining_pool.extend([row for row in candidates if int(row["id"]) not in picked_ids])
        else:
            sorted_candidates = sorted(
                candidates,
                key=lambda row: adaptive_selection_score(exposures.get(int(row["id"])), rng),
                reverse=True,
            )
            selected.extend(sorted_candidates[:target])
            remaining_pool.extend(sorted_candidates[target:])

    if len(selected) < count:
        selected_ids = {int(row["id"]) for row in selected}
        fallback = select_complete_units(
            [row for row in remaining_pool if int(row["id"]) not in selected_ids],
            count - len(selected),
            exposures,
            rng,
        )
        selected.extend(fallback)

    return selected


def question_type_for_target(target_type: str, target_code: str) -> str:
    if target_type == "question_type":
        if target_code not in QUESTION_TYPE_NAMES:
            raise ValueError(f"不支持的专项题型：{target_code}")
        return target_code
    prefix = target_code.split(".", 1)[0]
    mapping = {
        "grammar": "grammar_choice",
        "literature": "literature_choice",
        "culture": "culture_choice",
        "reading": "reading_choice",
        "listening": "listening_choice",
    }
    if prefix not in mapping:
        raise ValueError(f"不支持的专项知识点：{target_code}")
    return mapping[prefix]


def resolve_knowledge_target(
    conn: sqlite3.Connection,
    exam_system_id: int,
    level_id: int,
    target_code: str,
) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT kp.code, kp.name_zh
        FROM knowledge_points kp
        WHERE kp.code = ?
          AND (kp.exam_system_id = ? OR kp.exam_system_id IS NULL)
          AND EXISTS (
            SELECT 1
            FROM question_knowledge_points qkp
            JOIN questions q ON q.id = qkp.question_id
            WHERE qkp.knowledge_point_id = kp.id
              AND q.exam_system_id = ? AND q.level_id = ?
              AND q.review_status = 'approved' AND q.source_usage = 'practice'
          )
        ORDER BY CASE WHEN kp.exam_system_id = ? THEN 0 ELSE 1 END
        LIMIT 1
        """,
        (target_code, exam_system_id, exam_system_id, level_id, exam_system_id),
    ).fetchone()
    if row is None:
        raise ValueError("当前考试没有这个可练知识点。")
    return {
        "target_type": "knowledge_point",
        "target_code": row["code"],
        "target_name_zh": row["name_zh"],
        "reason": "由学生从知识画像中选择",
        "count": 10,
    }


def fetch_quiz_rows(
    conn: sqlite3.Connection,
    filters: list[str],
    params: list[Any],
) -> list[sqlite3.Row]:
    return conn.execute(
        f"""
        SELECT
          q.id,
          q.source_year,
          q.source_question_number,
          q.source_label,
          q.requires_source_label,
          q.content_origin,
          q.stem,
          qt.code AS question_type,
          p.id AS passage_id,
          p.title AS passage_title,
          p.body AS passage_body
        FROM questions q
        JOIN question_types qt ON qt.id = q.question_type_id
        LEFT JOIN passages p ON p.id = q.passage_id
        WHERE {" AND ".join(filters)}
        ORDER BY q.source_year, CAST(q.source_question_number AS INTEGER), q.id
        """,
        params,
    ).fetchall()


def api_generate_quiz(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = normalize_user_id(payload.get("user_id"))
    count = max(1, min(int(payload.get("count") or 10), 50))
    mode = str(payload.get("mode") or "random")
    if mode not in {"random", "diagnostic", "weakness_review", "knowledge_point", "wrongbook_review"}:
        raise ValueError(f"不支持的组卷模式：{mode}")
    exam_system_code = str(payload.get("exam_system") or "TEM8_RU")
    level_code = str(payload.get("level") or "TEM8")
    question_types = [str(item) for item in payload.get("question_types", []) if item]
    if mode == "diagnostic" and not question_types:
        question_types = DIAGNOSTIC_QUESTION_TYPES
    if not question_types:
        question_types = DEFAULT_RANDOM_QUESTION_TYPES
    years = [int(item) for item in payload.get("years", []) if item]
    seed = payload.get("seed")
    rng = random.Random(seed)
    training: dict[str, Any] | None = None

    with db() as conn:
        user = ensure_user_exists(conn, user_id)
        exam_system_id, level_id = fetch_ids(conn, exam_system_code, level_code)
        base_filters = [
            "q.review_status = 'approved'",
            "q.source_usage = 'practice'",
            "q.exam_system_id = ?",
            "q.level_id = ?",
        ]
        base_params: list[Any] = [exam_system_id, level_id]

        if mode == "wrongbook_review":
            requested_ids = list(
                dict.fromkeys(
                    int(item)
                    for item in payload.get("question_ids", [])
                    if str(item).strip().isdigit() and int(item) > 0
                )
            )
            wrongbook_filters = [
                *base_filters,
                """
                EXISTS (
                  SELECT 1 FROM question_exposures qe
                  WHERE qe.user_id = ? AND qe.question_id = q.id AND qe.wrong_count > 0
                )
                """,
            ]
            wrongbook_params = [*base_params, user_id]
            if requested_ids:
                placeholders = ", ".join("?" for _ in requested_ids)
                wrongbook_filters.append(f"q.id IN ({placeholders})")
                wrongbook_params.extend(requested_ids)
            else:
                wrongbook_filters.append(
                    """
                    EXISTS (
                      SELECT 1 FROM question_exposures qe2
                      WHERE qe2.user_id = ? AND qe2.question_id = q.id
                        AND qe2.last_is_correct = 0
                    )
                    """
                )
                wrongbook_params.append(user_id)
            wrong_rows = fetch_quiz_rows(conn, wrongbook_filters, wrongbook_params)
            found_ids = {int(row["id"]) for row in wrong_rows}
            if requested_ids and found_ids != set(requested_ids):
                raise ValueError("所选题目中包含不属于当前账号或当前考试的错题。")
            if not wrong_rows:
                raise ValueError("当前条件下没有可重练的错题。")

            exposures = exposure_rows(conn, user_id, list(found_ids))
            selected_wrong = select_complete_units(wrong_rows, min(count, len(wrong_rows)), exposures, rng)
            reading_passage_ids = sorted(
                {
                    int(row["passage_id"])
                    for row in selected_wrong
                    if row["question_type"] == READING_QUESTION_TYPE and row["passage_id"]
                }
            )
            selected_by_id = {int(row["id"]): row for row in selected_wrong}
            if reading_passage_ids:
                placeholders = ", ".join("?" for _ in reading_passage_ids)
                passage_rows = fetch_quiz_rows(
                    conn,
                    [*base_filters, f"q.passage_id IN ({placeholders})"],
                    [*base_params, *reading_passage_ids],
                )
                selected_by_id.update({int(row["id"]): row for row in passage_rows})
            selected = sorted(
                selected_by_id.values(),
                key=lambda row: (
                    row["source_year"] or 9999,
                    int(row["passage_id"] or 0),
                    source_question_number(row),
                    int(row["id"]),
                ),
            )
            training = {
                "target_type": "wrongbook",
                "target_code": "wrongbook.pending",
                "target_name_zh": "错题重练",
                "reason": "由学生错题本生成",
                "count": len(selected),
                "question_type": "mixed",
                "fallback_used": False,
                "selected_wrong_count": len(selected_wrong),
                "expanded_reading_count": len(selected) - len(selected_wrong),
            }
        elif mode in {"weakness_review", "knowledge_point"}:
            if mode == "weakness_review":
                daily_task_id = int(payload.get("daily_task_id") or 0)
                if daily_task_id:
                    daily_task = conn.execute(
                        """
                        SELECT dst.*
                        FROM daily_study_tasks dst
                        JOIN daily_study_plans dsp ON dsp.id = dst.plan_id
                        WHERE dst.id = ? AND dst.task_type = 'questions'
                          AND dsp.user_id = ? AND dsp.exam_system_id = ? AND dsp.level_id = ?
                          AND dsp.plan_date = date('now', 'localtime')
                        """,
                        (daily_task_id, user_id, exam_system_id, level_id),
                    ).fetchone()
                    if daily_task is None:
                        raise ValueError("今日学习任务不存在或不属于当前账号。")
                    recommendation = {
                        "target_type": daily_task["target_type"],
                        "target_code": daily_task["target_code"],
                        "target_name_zh": daily_task["target_name_zh"],
                        "reason": daily_task["reason"],
                        "count": int(daily_task["target_count"] or count),
                        "daily_task_id": daily_task_id,
                    }
                else:
                    profile = recalculate_profile(conn, user_id, exam_system_code, level_code)
                    recommendation = profile.get("next_training")
                    if not recommendation:
                        raise ValueError("当前作答数据还不足以生成薄弱专项，请先完成入门诊断。")
            else:
                target_code_value = str(payload.get("target_code") or "").strip()
                if not target_code_value:
                    raise ValueError("请选择要训练的知识点。")
                recommendation = resolve_knowledge_target(
                    conn,
                    exam_system_id,
                    level_id,
                    target_code_value,
                )
            target_type = str(recommendation["target_type"])
            target_code = str(recommendation["target_code"])
            target_question_type = question_type_for_target(target_type, target_code)

            broad_filters = [*base_filters, "qt.code = ?"]
            broad_params = [*base_params, target_question_type]
            broad_rows = fetch_quiz_rows(conn, broad_filters, broad_params)
            if not broad_rows:
                raise ValueError("当前专项没有可用的已审核题目。")

            exact_filters = list(base_filters)
            exact_params = list(base_params)
            if target_type == "knowledge_point":
                if target_question_type == READING_QUESTION_TYPE:
                    exact_filters.append(
                        """
                        q.passage_id IN (
                          SELECT DISTINCT q2.passage_id
                          FROM questions q2
                          JOIN question_knowledge_points qkp2 ON qkp2.question_id = q2.id
                          JOIN knowledge_points kp2 ON kp2.id = qkp2.knowledge_point_id
                          WHERE q2.exam_system_id = ? AND q2.level_id = ?
                            AND q2.passage_id IS NOT NULL AND kp2.code = ?
                        )
                        """
                    )
                    exact_params.extend([exam_system_id, level_id, target_code])
                else:
                    exact_filters.append(
                        """
                        EXISTS (
                          SELECT 1
                          FROM question_knowledge_points qkp2
                          JOIN knowledge_points kp2 ON kp2.id = qkp2.knowledge_point_id
                          WHERE qkp2.question_id = q.id AND kp2.code = ?
                        )
                        """
                    )
                    exact_params.append(target_code)
            else:
                exact_filters.append("qt.code = ?")
                exact_params.append(target_question_type)

            exact_rows = fetch_quiz_rows(conn, exact_filters, exact_params)
            all_rows_by_id = {int(row["id"]): row for row in [*exact_rows, *broad_rows]}
            exposures = exposure_rows(conn, user_id, list(all_rows_by_id))
            selected = select_complete_units(exact_rows, count, exposures, rng)
            exact_ids = {int(row["id"]) for row in exact_rows}
            if len(selected) < count:
                selected_ids = {int(row["id"]) for row in selected}
                fallback_rows = [row for row in broad_rows if int(row["id"]) not in selected_ids]
                selected.extend(select_complete_units(fallback_rows, count - len(selected), exposures, rng))
            fallback_used = any(int(row["id"]) not in exact_ids for row in selected)
            training = {
                **recommendation,
                "question_type": target_question_type,
                "fallback_used": fallback_used,
                "exact_pool_count": len(exact_rows),
                "available_type_count": len(broad_rows),
            }
        else:
            filters = list(base_filters)
            params = list(base_params)
            if question_types:
                placeholders = ", ".join("?" for _ in question_types)
                filters.append(f"qt.code IN ({placeholders})")
                params.extend(question_types)
            if years:
                placeholders = ", ".join("?" for _ in years)
                filters.append(f"q.source_year IN ({placeholders})")
                params.extend(years)
            rows = fetch_quiz_rows(conn, filters, params)
            if len(rows) < count:
                raise ValueError(f"当前条件下只有 {len(rows)} 道题，无法生成 {count} 道。")
            exposures = exposure_rows(conn, user_id, [int(row["id"]) for row in rows])
            if mode == "diagnostic":
                selected = select_balanced_by_type(rows, count, question_types, exposures, rng)
            else:
                selected = select_complete_units(rows, count, exposures, rng)
        questions = [
            public_question(conn, row, index)
            for index, row in enumerate(selected, start=1)
        ]
    return {
        "exam_system": exam_system_code,
        "level": level_code,
        "mode": mode,
        "user": public_user(user),
        "count": len(questions),
        "questions": questions,
        "training": training,
    }


def period_answer_summary(
    conn: sqlite3.Connection,
    user_id: int,
    exam_system_id: int,
    level_id: int,
    days: int,
) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT
          COUNT(*) AS attempted,
          COALESCE(SUM(CASE WHEN ua.is_correct = 1 THEN 1 ELSE 0 END), 0) AS correct,
          COUNT(DISTINCT qi.quiz_session_id) AS sessions
        FROM user_answers ua
        JOIN quiz_items qi ON qi.id = ua.quiz_item_id
        JOIN quiz_sessions qs ON qs.id = qi.quiz_session_id
        WHERE ua.user_id = ?
          AND qs.exam_system_id = ? AND qs.level_id = ?
          AND datetime(ua.answered_at) >= datetime('now', 'localtime', ?)
        """,
        (user_id, exam_system_id, level_id, f"-{days} days"),
    ).fetchone()
    attempted = int(row["attempted"] or 0)
    correct = int(row["correct"] or 0)
    return {
        "days": days,
        "attempted": attempted,
        "correct": correct,
        "sessions": int(row["sessions"] or 0),
        "accuracy": round(correct / attempted, 4) if attempted else None,
    }


def daily_answer_trend(
    conn: sqlite3.Connection,
    user_id: int,
    exam_system_id: int,
    level_id: int,
    days: int = 7,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        WITH RECURSIVE dates(day, offset) AS (
          SELECT date('now', 'localtime', ?), 0
          UNION ALL
          SELECT date(day, '+1 day'), offset + 1 FROM dates WHERE offset < ?
        ), answers AS (
          SELECT
            date(ua.answered_at, 'localtime') AS day,
            COUNT(*) AS attempted,
            SUM(CASE WHEN ua.is_correct = 1 THEN 1 ELSE 0 END) AS correct
          FROM user_answers ua
          JOIN quiz_items qi ON qi.id = ua.quiz_item_id
          JOIN quiz_sessions qs ON qs.id = qi.quiz_session_id
          WHERE ua.user_id = ?
            AND qs.exam_system_id = ? AND qs.level_id = ?
            AND date(ua.answered_at, 'localtime') >= date('now', 'localtime', ?)
          GROUP BY date(ua.answered_at, 'localtime')
        )
        SELECT dates.day, COALESCE(answers.attempted, 0) AS attempted,
               COALESCE(answers.correct, 0) AS correct
        FROM dates
        LEFT JOIN answers ON answers.day = dates.day
        ORDER BY dates.day
        """,
        (f"-{days - 1} days", days - 1, user_id, exam_system_id, level_id, f"-{days - 1} days"),
    ).fetchall()
    return [
        {
            "date": row["day"],
            "attempted": int(row["attempted"] or 0),
            "correct": int(row["correct"] or 0),
            "accuracy": round(int(row["correct"] or 0) / int(row["attempted"]), 4)
            if int(row["attempted"] or 0)
            else None,
        }
        for row in rows
    ]


def create_or_load_daily_plan(
    conn: sqlite3.Connection,
    user_id: int,
    exam_system_id: int,
    level_id: int,
    profile: dict[str, Any],
    word_status: dict[str, Any],
    pending_wrong: int,
) -> sqlite3.Row:
    plan_date = datetime.now().strftime("%Y-%m-%d")
    plan = conn.execute(
        """
        SELECT * FROM daily_study_plans
        WHERE user_id = ? AND exam_system_id = ? AND level_id = ? AND plan_date = ?
        """,
        (user_id, exam_system_id, level_id, plan_date),
    ).fetchone()
    if plan is not None:
        return plan

    cursor = conn.execute(
        """
        INSERT INTO daily_study_plans (user_id, exam_system_id, level_id, plan_date)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, exam_system_id, level_id, plan_date),
    )
    plan_id = int(cursor.lastrowid)
    recommended = profile.get("next_training")
    if recommended:
        target_type = str(recommended["target_type"])
        target_code = str(recommended["target_code"])
        target_question_type = question_type_for_target(target_type, target_code)
        question_task = (
            "薄弱专项",
            int(recommended.get("count", 10)),
            "weakness_review",
            target_type,
            target_code,
            str(recommended.get("target_name_zh") or "薄弱知识点"),
            target_question_type,
            str(recommended.get("reason") or "根据近期作答表现推荐"),
        )
    else:
        question_task = (
            "入门诊断",
            30,
            "diagnostic",
            "diagnostic",
            "diagnostic.initial",
            "建立初始能力画像",
            None,
            "当前作答数据不足，先用四类题目建立能力基线",
        )

    due_count = int(word_status.get("due_count") or 0)
    new_count = int(word_status.get("new_count") or 0)
    word_target = min(due_count, 20) if due_count else min(new_count, 20)
    word_label = "到期单词复习" if due_count else "今日新词"
    word_reason = (
        f"有 {due_count} 个单词到达复习时间"
        if due_count
        else "用少量新词保持稳定积累" if word_target else "当前词库任务已完成"
    )
    wrong_target = min(pending_wrong, 5)
    wrong_reason = (
        f"优先消化最近仍未答对的 {pending_wrong} 道错题"
        if pending_wrong
        else "当前没有待巩固错题"
    )
    rows = [
        (
            plan_id, "questions", 1, question_task[0], question_task[1], question_task[2],
            question_task[3], question_task[4], question_task[5], question_task[6],
            question_task[7], 0,
        ),
        (
            plan_id, "wrongbook", 2, "错题回炉", wrong_target, "wrongbook_review",
            "wrongbook", "wrongbook.pending", "待巩固错题", None,
            wrong_reason, pending_wrong,
        ),
        (
            plan_id, "words", 3, word_label, word_target,
            "review" if due_count else "mixed", "vocabulary", "vocabulary.daily",
            "到期复习" if due_count else "新词积累", None, word_reason, due_count,
        ),
    ]
    conn.executemany(
        """
        INSERT INTO daily_study_tasks (
          plan_id, task_type, sort_order, label, target_count, training_mode,
          target_type, target_code, target_name_zh, target_question_type,
          reason, baseline_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return conn.execute("SELECT * FROM daily_study_plans WHERE id = ?", (plan_id,)).fetchone()


def daily_question_progress(
    conn: sqlite3.Connection,
    plan: sqlite3.Row,
    task: sqlite3.Row,
) -> int:
    filters = [
        "ua.user_id = ?",
        "q.exam_system_id = ?",
        "q.level_id = ?",
        "date(ua.answered_at, 'localtime') = ?",
    ]
    params: list[Any] = [
        int(plan["user_id"]),
        int(plan["exam_system_id"]),
        int(plan["level_id"]),
        plan["plan_date"],
    ]
    if task["target_question_type"]:
        filters.append("qt.code = ?")
        params.append(task["target_question_type"])
    return int(
        conn.execute(
            f"""
            SELECT COUNT(*)
            FROM user_answers ua
            JOIN quiz_items qi ON qi.id = ua.quiz_item_id
            JOIN questions q ON q.id = qi.question_id
            JOIN question_types qt ON qt.id = q.question_type_id
            WHERE {" AND ".join(filters)}
            """,
            params,
        ).fetchone()[0]
    )


def daily_task_payloads(
    conn: sqlite3.Connection,
    plan: sqlite3.Row,
    word_status: dict[str, Any],
    pending_wrong: int,
) -> list[dict[str, Any]]:
    tasks = conn.execute(
        "SELECT * FROM daily_study_tasks WHERE plan_id = ? ORDER BY sort_order, id",
        (plan["id"],),
    ).fetchall()
    payloads = []
    for task in tasks:
        target = int(task["target_count"] or 0)
        if task["task_type"] == "questions":
            completed = daily_question_progress(conn, plan, task)
        elif task["task_type"] == "words":
            completed = int(word_status.get("reviewed_today") or 0)
        else:
            completed = max(int(task["baseline_count"] or 0) - pending_wrong, 0)
        completed = min(completed, target) if target else 0
        is_completed = target == 0 or completed >= target
        payloads.append(
            {
                "task_id": int(task["id"]),
                "task_type": task["task_type"],
                "label": task["label"],
                "target": target,
                "completed": completed,
                "remaining": max(target - completed, 0),
                "is_completed": is_completed,
                "mode": task["training_mode"],
                "target_code": task["target_code"],
                "target_name_zh": task["target_name_zh"],
                "reason": task["reason"],
            }
        )
    if payloads and all(item["is_completed"] for item in payloads):
        conn.execute(
            "UPDATE daily_study_plans SET status = 'completed', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (plan["id"],),
        )
    return payloads


def api_study_center(
    user_id: int = DEFAULT_USER_ID,
    exam_system_code: str = "TEM8_RU",
    level_code: str = "TEM8",
) -> dict[str, Any]:
    with db() as conn:
        user = ensure_user_exists(conn, user_id)
        exam_system_id, level_id = fetch_ids(conn, exam_system_code, level_code)
        profile = recalculate_profile(conn, user_id, exam_system_code, level_code)
        mastery_by_code = {
            item["target_code"]: item for item in profile.get("knowledge_mastery", [])
        }
        knowledge_rows = conn.execute(
            """
            SELECT
              kp.code, kp.name_zh, kp.category, kp.sort_order,
              COUNT(DISTINCT q.id) AS question_count
            FROM knowledge_points kp
            JOIN question_knowledge_points qkp ON qkp.knowledge_point_id = kp.id
            JOIN questions q ON q.id = qkp.question_id
            WHERE q.exam_system_id = ? AND q.level_id = ?
              AND q.review_status = 'approved' AND q.source_usage = 'practice'
              AND kp.category <> 'reading'
            GROUP BY kp.code, kp.name_zh, kp.category, kp.sort_order
            ORDER BY kp.category, kp.sort_order, kp.name_zh
            """,
            (exam_system_id, level_id),
        ).fetchall()
        knowledge_mastery = []
        for row in knowledge_rows:
            current = mastery_by_code.get(row["code"], {})
            knowledge_mastery.append(
                {
                    "target_code": row["code"],
                    "target_name_zh": row["name_zh"],
                    "category": row["category"],
                    "question_count": int(row["question_count"] or 0),
                    "attempt_count": int(current.get("attempt_count", 0)),
                    "wrong_count": int(current.get("wrong_count", 0)),
                    "mastery_score": int(current.get("mastery_score", 0)),
                    "mastery_status": current.get("mastery_status", "insufficient_data"),
                    "mastery_status_zh": current.get("mastery_status_zh", "数据不足"),
                }
            )

        word_status = api_word_status(user_id, exam_system_code, level_code)
        pending_wrong = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM question_exposures qe
                JOIN questions q ON q.id = qe.question_id
                WHERE qe.user_id = ? AND qe.wrong_count > 0 AND qe.last_is_correct = 0
                  AND q.exam_system_id = ? AND q.level_id = ?
                  AND q.review_status = 'approved' AND q.source_usage = 'practice'
                """,
                (user_id, exam_system_id, level_id),
            ).fetchone()[0]
        )
        seven_days = period_answer_summary(conn, user_id, exam_system_id, level_id, 7)
        thirty_days = period_answer_summary(conn, user_id, exam_system_id, level_id, 30)
        trend = daily_answer_trend(conn, user_id, exam_system_id, level_id)
        plan = create_or_load_daily_plan(
            conn,
            user_id,
            exam_system_id,
            level_id,
            profile,
            word_status,
            pending_wrong,
        )
        daily_tasks = daily_task_payloads(conn, plan, word_status, pending_wrong)

    recommended = profile.get("next_training")
    return {
        "user": public_user(user),
        "exam_system": exam_system_code,
        "level": level_code,
        "today": {
            "plan_id": int(plan["id"]),
            "plan_date": plan["plan_date"],
            "status": "completed" if daily_tasks and all(item["is_completed"] for item in daily_tasks) else "active",
            "completed_tasks": sum(1 for item in daily_tasks if item["is_completed"]),
            "task_count": len(daily_tasks),
            "tasks": daily_tasks,
        },
        "periods": {
            "seven_days": seven_days,
            "thirty_days": thirty_days,
        },
        "daily_trend": trend,
        "question_type_mastery": profile.get("question_type_mastery", []),
        "knowledge_mastery": knowledge_mastery,
        "next_training": recommended,
    }


def api_profile(user_id: int = DEFAULT_USER_ID, exam_system_code: str = "TEM8_RU", level_code: str = "TEM8") -> dict[str, Any]:
    with db() as conn:
        ensure_user_exists(conn, user_id)
        return recalculate_profile(conn, user_id, exam_system_code, level_code)


def latest_answer_for_question(conn: sqlite3.Connection, user_id: int, question_id: int) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT
          ua.selected_answer,
          ua.is_correct,
          ua.answered_at,
          qi.quiz_session_id
        FROM user_answers ua
        JOIN quiz_items qi ON qi.id = ua.quiz_item_id
        JOIN quiz_sessions qs ON qs.id = qi.quiz_session_id
        WHERE qi.question_id = ?
          AND COALESCE(ua.user_id, qs.user_id) = ?
        ORDER BY ua.answered_at DESC, ua.id DESC
        LIMIT 1
        """,
        (question_id, user_id),
    ).fetchone()


def api_wrongbook(
    user_id: int = DEFAULT_USER_ID,
    limit: int = 80,
    exam_system_code: str = "TEM8_RU",
    level_code: str = "TEM8",
) -> dict[str, Any]:
    limit = max(1, min(limit, 200))
    with db() as conn:
        user = ensure_user_exists(conn, user_id)
        exam_system_id, level_id = fetch_ids(conn, exam_system_code, level_code)
        rows = conn.execute(
            """
            SELECT
              q.id,
              q.source_year,
              q.source_question_number,
              q.source_label,
              q.requires_source_label,
              q.content_origin,
              q.stem,
              q.correct_answer,
              qt.code AS question_type,
              p.id AS passage_id,
              p.title AS passage_title,
              p.body AS passage_body,
              qe.seen_count,
              qe.correct_count,
              qe.wrong_count,
              qe.last_is_correct,
              qe.first_seen_at,
              qe.last_seen_at,
              COALESCE(wp.note_text, '') AS note_text,
              COALESCE(wp.is_favorite, 0) AS is_favorite
            FROM question_exposures qe
            JOIN questions q ON q.id = qe.question_id
            JOIN question_types qt ON qt.id = q.question_type_id
            LEFT JOIN passages p ON p.id = q.passage_id
            LEFT JOIN wrongbook_preferences wp
              ON wp.user_id = qe.user_id AND wp.question_id = qe.question_id
            WHERE qe.user_id = ?
              AND qe.wrong_count > 0
              AND q.review_status = 'approved'
              AND q.source_usage = 'practice'
              AND q.exam_system_id = ?
              AND q.level_id = ?
            ORDER BY
              CASE WHEN qe.last_is_correct = 0 THEN 0 ELSE 1 END,
              datetime(qe.last_seen_at) DESC,
              qe.wrong_count DESC,
              q.id
            LIMIT ?
            """,
            (user_id, exam_system_id, level_id, limit),
        ).fetchall()
        items = []
        pending_count = 0
        corrected_count = 0
        favorite_count = 0
        repeat_wrong_count = 0
        for index, row in enumerate(rows, start=1):
            latest = latest_answer_for_question(conn, user_id, int(row["id"]))
            item = public_question(conn, row, index)
            last_is_correct = bool(row["last_is_correct"]) if row["last_is_correct"] is not None else False
            if last_is_correct:
                corrected_count += 1
            else:
                pending_count += 1
            favorite_count += int(bool(row["is_favorite"]))
            repeat_wrong_count += int(int(row["wrong_count"] or 0) >= 2)
            knowledge = conn.execute(
                """
                SELECT kp.code, kp.name_zh, kp.category
                FROM question_knowledge_points qkp
                JOIN knowledge_points kp ON kp.id = qkp.knowledge_point_id
                WHERE qkp.question_id = ?
                ORDER BY kp.sort_order, kp.code
                """,
                (int(row["id"]),),
            ).fetchall()
            item.update(
                {
                    "correct_answer": row["correct_answer"],
                    "selected_answer": latest["selected_answer"] if latest else "",
                    "latest_is_correct": bool(latest["is_correct"]) if latest else last_is_correct,
                    "latest_answered_at": latest["answered_at"] if latest else row["last_seen_at"],
                    "latest_quiz_session_id": latest["quiz_session_id"] if latest else None,
                    "seen_count": row["seen_count"],
                    "correct_count": row["correct_count"],
                    "wrong_count": row["wrong_count"],
                    "first_seen_at": row["first_seen_at"],
                    "last_seen_at": row["last_seen_at"],
                    "status": "corrected" if last_is_correct else "pending",
                    "status_zh": "已订正" if last_is_correct else "待巩固",
                    "is_repeat_wrong": int(row["wrong_count"] or 0) >= 2,
                    "is_favorite": bool(row["is_favorite"]),
                    "note_text": row["note_text"] or "",
                    "knowledge_points": [
                        {
                            "code": point["code"],
                            "name_zh": point["name_zh"],
                            "category": point["category"],
                        }
                        for point in knowledge
                    ],
                }
            )
            items.append(item)
        type_filters = []
        for code, name in QUESTION_TYPE_NAMES.items():
            count = sum(1 for item in items if item["question_type"] == code)
            if count:
                type_filters.append({"code": code, "name_zh": name, "count": count})
        knowledge_filters: dict[str, dict[str, Any]] = {}
        for item in items:
            for point in item["knowledge_points"]:
                current = knowledge_filters.setdefault(
                    point["code"],
                    {**point, "count": 0},
                )
                current["count"] += 1
    return {
        "user": public_user(user),
        "exam_system": exam_system_code,
        "level": level_code,
        "count": len(items),
        "pending_count": pending_count,
        "corrected_count": corrected_count,
        "favorite_count": favorite_count,
        "repeat_wrong_count": repeat_wrong_count,
        "filters": {
            "question_types": type_filters,
            "knowledge_points": sorted(
                knowledge_filters.values(),
                key=lambda item: (item["category"], item["name_zh"]),
            ),
        },
        "items": items,
    }


def api_update_wrongbook_item(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = normalize_user_id(payload.get("user_id"))
    question_id = int(payload.get("question_id") or 0)
    if question_id <= 0:
        raise ValueError("错题编号无效。")
    note_text = str(payload.get("note_text") or "").strip()
    if len(note_text) > 1000:
        raise ValueError("错题笔记不要超过 1000 字。")
    is_favorite = 1 if bool(payload.get("is_favorite")) else 0
    with db() as conn:
        exists = conn.execute(
            """
            SELECT 1
            FROM question_exposures
            WHERE user_id = ? AND question_id = ? AND wrong_count > 0
            """,
            (user_id, question_id),
        ).fetchone()
        if exists is None:
            raise ValueError("这道题不在当前账号的错题本中。")
        conn.execute(
            """
            INSERT INTO wrongbook_preferences (user_id, question_id, note_text, is_favorite)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, question_id) DO UPDATE SET
              note_text = excluded.note_text,
              is_favorite = excluded.is_favorite,
              updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, question_id, note_text or None, is_favorite),
        )
    return {
        "status": "ok",
        "question_id": question_id,
        "note_text": note_text,
        "is_favorite": bool(is_favorite),
    }


def fetch_ids(conn: sqlite3.Connection, exam_system_code: str = "TEM8_RU", level_code: str = "TEM8") -> tuple[int, int]:
    row = conn.execute("SELECT id FROM exam_systems WHERE code = ?", (exam_system_code,)).fetchone()
    if row is None:
        raise ValueError(f"Unknown exam system: {exam_system_code}")
    exam_system_id = int(row[0])
    row = conn.execute("SELECT id FROM exam_levels WHERE exam_system_id = ? AND code = ?", (exam_system_id, level_code)).fetchone()
    if row is None:
        raise ValueError(f"Unknown exam level: {level_code}")
    return exam_system_id, int(row[0])

def summary_for_code(code: str, attempted: int, wrong: int) -> str:
    name = KNOWLEDGE_NAMES.get(code, code)
    if wrong == 0:
        return f"{name}: 本次全部答对，保持节奏。"
    return f"{name}: 本次 {attempted} 题中错 {wrong} 题，建议先回看错题，再做同类巩固。"


def api_grade(payload: dict[str, Any]) -> dict[str, Any]:
    submitted_answers = payload.get("answers") or []
    if not submitted_answers:
        raise ValueError("还没有收到答案。")
    user_id = normalize_user_id(payload.get("user_id"))
    session_mode = str(payload.get("mode") or "random")
    if session_mode not in {"random", "knowledge_point", "weakness_review", "mock_exam"}:
        raise ValueError(f"不支持的练习记录类型：{session_mode}")

    with db() as conn:
        ensure_user_exists(conn, user_id)
        exam_system_code = str(payload.get("exam_system") or "TEM8_RU")
        level_code = str(payload.get("level") or "TEM8")
        exam_system_id, level_id = fetch_ids(conn, exam_system_code, level_code)
        cursor = conn.execute(
            """
            INSERT INTO quiz_sessions (
              user_id, exam_system_id, level_id, title, mode, status, total_questions
            )
            VALUES (?, ?, ?, ?, ?, 'submitted', ?)
            """,
            (
                user_id,
                exam_system_id,
                level_id,
                payload.get("title") or "TEM8 student practice",
                session_mode,
                len(submitted_answers),
            ),
        )
        quiz_session_id = int(cursor.lastrowid)

        correct_count = 0
        wrong_questions: list[dict[str, Any]] = []
        graded_questions: list[dict[str, Any]] = []
        weakness: dict[str, dict[str, Any]] = {}

        for item in submitted_answers:
            quiz_number = int(item["quiz_number"])
            question_id = int(item["question_id"])
            selected_answer = str(item.get("selected_answer") or "").strip().upper()
            row = fetch_question(conn, question_id)
            if int(row["exam_system_id"]) != exam_system_id or int(row["level_id"]) != level_id:
                raise ValueError("提交的题目不属于当前考试范围。")
            correct_answer = str(row["correct_answer"] or "").strip().upper()
            is_correct = selected_answer == correct_answer
            if is_correct:
                correct_count += 1

            cursor = conn.execute(
                """
                INSERT INTO quiz_items (quiz_session_id, question_id, sort_order)
                VALUES (?, ?, ?)
                """,
                (quiz_session_id, question_id, quiz_number),
            )
            quiz_item_id = int(cursor.lastrowid)
            conn.execute(
                """
                INSERT INTO user_answers (quiz_item_id, user_id, selected_answer, is_correct)
                VALUES (?, ?, ?, ?)
                """,
                (quiz_item_id, user_id, selected_answer or None, 1 if is_correct else 0),
            )
            record_question_exposure(conn, user_id, quiz_session_id, question_id, is_correct)

            codes = knowledge_codes(conn, question_id)
            for code in codes:
                bucket = weakness.setdefault(
                    code,
                    {
                        "knowledge_point_code": code,
                        "knowledge_point_name_zh": KNOWLEDGE_NAMES.get(code, code),
                        "attempted_count": 0,
                        "wrong_count": 0,
                        "wrong_question_numbers": [],
                    },
                )
                bucket["attempted_count"] += 1
                if not is_correct:
                    bucket["wrong_count"] += 1
                    bucket["wrong_question_numbers"].append(quiz_number)

            graded = public_question(conn, row, quiz_number)
            graded["selected_answer"] = selected_answer
            graded["correct_answer"] = correct_answer
            graded["is_correct"] = is_correct
            graded_questions.append(graded)

            if not is_correct:
                wrong_questions.append(graded)

        total = len(submitted_answers)
        accuracy = correct_count / total if total else 0.0
        weakness_rows = []
        for item in sorted(weakness.values(), key=lambda row: (-row["wrong_count"], row["knowledge_point_code"])):
            attempted = int(item["attempted_count"])
            wrong = int(item["wrong_count"])
            item["accuracy"] = round((attempted - wrong) / attempted, 4) if attempted else 0
            item["advice_zh"] = summary_for_code(item["knowledge_point_code"], attempted, wrong)
            weakness_rows.append(item)

            kp = conn.execute(
                "SELECT id FROM knowledge_points WHERE code = ?",
                (item["knowledge_point_code"],),
            ).fetchone()
            if kp:
                conn.execute(
                    """
                    INSERT INTO weakness_snapshots (
                      user_id, quiz_session_id, knowledge_point_id, attempted_count,
                      wrong_count, accuracy, ai_summary_zh
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        quiz_session_id,
                        int(kp["id"]),
                        attempted,
                        wrong,
                        item["accuracy"],
                        item["advice_zh"],
                    ),
                )

        conn.execute(
            """
            UPDATE quiz_sessions
            SET status = 'reviewed',
                correct_count = ?,
                accuracy = ?,
                submitted_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (correct_count, accuracy, quiz_session_id),
        )
        conn.commit()

    result = {
        "quiz_session_id": quiz_session_id,
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
        "total_questions": total,
        "correct_count": correct_count,
        "wrong_count": total - correct_count,
        "accuracy": round(accuracy, 4),
        "weakness": weakness_rows,
        "wrong_questions": wrong_questions,
        "graded_questions": graded_questions,
    }
    with db() as conn:
        result["profile"] = recalculate_profile(conn, user_id, exam_system_code, level_code)
    if result["wrong_count"]:
        try:
            result["explanation"] = generate_explanation_for_session(quiz_session_id)
        except Exception as exc:
            result["explanation_error"] = str(exc)
    else:
        result["explanation"] = {
            "quiz_session_id": quiz_session_id,
            "thread_id": None,
            "assistant_text": "本次无错题。",
            "question_explanations": [],
            "study_advice_zh": "本次无错题。可以继续生成新练习，或选择薄弱专项保持手感。",
        }
    return result


def grading_report_for_session(conn: sqlite3.Connection, quiz_session_id: int) -> dict[str, Any]:
    session = conn.execute(
        """
        SELECT id, user_id, total_questions, correct_count, accuracy, submitted_at
        FROM quiz_sessions
        WHERE id = ?
        """,
        (quiz_session_id,),
    ).fetchone()
    if session is None:
        raise ValueError(f"没有找到测试记录 {quiz_session_id}。")

    rows = conn.execute(
        """
        SELECT qi.sort_order, qi.question_id, ua.selected_answer, ua.is_correct
        FROM quiz_items qi
        JOIN user_answers ua ON ua.quiz_item_id = qi.id
        WHERE qi.quiz_session_id = ?
        ORDER BY qi.sort_order
        """,
        (quiz_session_id,),
    ).fetchall()
    if not rows:
        raise ValueError(f"测试记录 {quiz_session_id} 还没有答题数据。")

    graded_questions = []
    wrong_questions = []
    for row in rows:
        question = fetch_question(conn, int(row["question_id"]))
        graded = public_question(conn, question, int(row["sort_order"]))
        graded["selected_answer"] = row["selected_answer"] or ""
        graded["correct_answer"] = question["correct_answer"]
        graded["is_correct"] = bool(row["is_correct"])
        graded_questions.append(graded)
        if not graded["is_correct"]:
            wrong_questions.append(graded)

    weakness = [
        {
            "knowledge_point_code": row["code"],
            "knowledge_point_name_zh": row["name_zh"],
            "attempted_count": row["attempted_count"],
            "wrong_count": row["wrong_count"],
            "accuracy": row["accuracy"],
            "advice_zh": row["ai_summary_zh"],
        }
        for row in conn.execute(
            """
            SELECT kp.code, kp.name_zh, ws.attempted_count, ws.wrong_count, ws.accuracy, ws.ai_summary_zh
            FROM weakness_snapshots ws
            JOIN knowledge_points kp ON kp.id = ws.knowledge_point_id
            WHERE ws.quiz_session_id = ?
            ORDER BY ws.wrong_count DESC, kp.code
            """,
            (quiz_session_id,),
        ).fetchall()
    ]

    return {
        "quiz_session_id": quiz_session_id,
        "user_id": session["user_id"],
        "submitted_at": session["submitted_at"],
        "total_questions": session["total_questions"],
        "correct_count": session["correct_count"],
        "wrong_count": len(wrong_questions),
        "accuracy": session["accuracy"],
        "weakness": weakness,
        "wrong_questions": wrong_questions,
        "graded_questions": graded_questions,
    }


def build_tutor_payload(report: dict[str, Any]) -> dict[str, Any]:
    wrong_questions = report["wrong_questions"]
    return {
        "grading_report": {
            "quiz_session_id": report["quiz_session_id"],
            "total_questions": report["total_questions"],
            "correct_count": report["correct_count"],
            "wrong_count": report["wrong_count"],
            "accuracy": report["accuracy"],
            "weakness": report["weakness"],
            "wrong_questions": wrong_questions,
        },
        "remediation_pack": {
            "summary_zh": "请根据错题题型、选项和薄弱知识点生成中文讲解、薄弱点排序、复习路径和可追问问题，不要输出巩固练习安排。",
            "remediation": [
                {
                    "knowledge_point_code": item["knowledge_point_code"],
                    "knowledge_point_name_zh": item["knowledge_point_name_zh"],
                    "attempted_count": item["attempted_count"],
                    "wrong_count": item["wrong_count"],
                    "accuracy": item["accuracy"],
                    "advice_zh": item["advice_zh"],
                    "practice_questions": [],
                }
                for item in report["weakness"]
                if int(item["wrong_count"]) > 0
            ],
        },
    }


def latest_assistant_text(conn: sqlite3.Connection, thread_id: int) -> str | None:
    row = conn.execute(
        """
        SELECT content
        FROM ai_tutor_messages
        WHERE thread_id = ? AND role = 'assistant'
        ORDER BY id DESC
        LIMIT 1
        """,
        (thread_id,),
    ).fetchone()
    return row["content"] if row else None


def api_thread(thread_id: int, user_id: int = DEFAULT_USER_ID) -> dict[str, Any]:
    with db() as conn:
        ensure_user_exists(conn, user_id)
        thread = conn.execute(
            """
            SELECT id, user_id, quiz_session_id, title, created_at, updated_at
            FROM ai_tutor_threads
            WHERE id = ?
            """,
            (thread_id,),
        ).fetchone()
        if thread is None:
            raise ValueError(f"没有找到 AI 对话线程 {thread_id}。")
        if thread["user_id"] is not None and int(thread["user_id"]) != user_id:
            raise ValueError("这个 AI 对话不属于当前学生。")
        messages = [
            dict(row)
            for row in conn.execute(
                """
                SELECT id, role, content, created_at
                FROM ai_tutor_messages
                WHERE thread_id = ? AND role = 'assistant'
                ORDER BY id
                """,
                (thread_id,),
            ).fetchall()
        ]
    return {"thread": dict(thread), "messages": messages}


def deepseek_chat(messages: list[dict[str, str]]) -> dict[str, Any]:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DeepSeek API Key 尚未配置。")
    body = {
        "model": os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL),
        "messages": messages,
        "thinking": {"type": os.environ.get("DEEPSEEK_THINKING", "disabled")},
        "reasoning_effort": os.environ.get("DEEPSEEK_REASONING_EFFORT", "high"),
        "stream": False,
    }
    request = urllib.request.Request(
        f"{os.environ.get('DEEPSEEK_BASE_URL', DEFAULT_BASE_URL).rstrip('/')}/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(exc.read().decode("utf-8", errors="replace")) from exc


def assistant_text_from_response(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        raise ValueError("DeepSeek 没有返回可用讲解。")
    text = str(choices[0].get("message", {}).get("content") or "").strip()
    if not text:
        raise ValueError("DeepSeek 返回内容为空。")
    return text


def parse_assistant_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {}
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return {}
    return parsed if isinstance(parsed, dict) else {}


def clean_selection_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    text = text.strip(".,!?;:()[]{}<>\"'«»„“”`—–…")
    if not text:
        raise ValueError("请先选中一个俄语单词或短语。")
    if len(text) > 80 or len(text.split()) > 6:
        raise ValueError("一次最多翻译 6 个词。")
    if not re.search(r"[А-Яа-яЁё]", text):
        raise ValueError("当前只支持俄语单词和短语。")
    if re.search(r"[^А-Яа-яЁё\-\s]", text):
        raise ValueError("请选择完整的俄语单词或短语。")
    return text


def clean_selection_context(value: Any, selected_text: str) -> str:
    context = re.sub(r"\s+", " ", str(value or "").strip())
    if not context:
        return selected_text
    if len(context) <= 500:
        return context
    position = context.casefold().find(selected_text.casefold())
    if position < 0:
        return context[:500]
    start = max(position - 220, 0)
    end = min(position + len(selected_text) + 220, len(context))
    return context[start:end]


def russian_normal_forms(selected_text: str) -> list[str]:
    global _MORPH_ANALYZER, _MORPH_UNAVAILABLE
    if " " in selected_text or _MORPH_UNAVAILABLE:
        return []
    if _MORPH_ANALYZER is None:
        try:
            import pymorphy3
        except ImportError:
            _MORPH_UNAVAILABLE = True
            return []
        _MORPH_ANALYZER = pymorphy3.MorphAnalyzer()
    forms = []
    for parsed in _MORPH_ANALYZER.parse(selected_text.lower())[:4]:
        normal_form = str(parsed.normal_form or "").strip()
        if normal_form and normal_form not in forms:
            forms.append(normal_form)
    return forms


def local_selection_translation(
    conn: sqlite3.Connection,
    selected_text: str,
    exam_system_id: int,
    level_id: int,
) -> dict[str, Any] | None:
    candidates = list(
        dict.fromkeys(
            [selected_text, selected_text.lower(), selected_text.capitalize(), *russian_normal_forms(selected_text)]
        )
    )
    placeholders = ", ".join("?" for _ in candidates)
    rows = conn.execute(
        f"""
        SELECT DISTINCT
          vi.id, vi.word, vi.lemma, vi.part_of_speech, vi.meaning_zh,
          CASE
            WHEN vi.word IN ({placeholders}) THEN 0
            WHEN COALESCE(vi.lemma, '') IN ({placeholders}) THEN 1
            ELSE 2
          END AS match_rank
        FROM vocabulary_items vi
        LEFT JOIN vocabulary_forms vf
          ON vf.vocabulary_item_id = vi.id AND vf.form_type = 'inflected_form'
        WHERE vi.exam_system_id = ? AND vi.level_id = ?
          AND vi.review_status = 'approved'
          AND (
            vi.word IN ({placeholders})
            OR COALESCE(vi.lemma, '') IN ({placeholders})
            OR COALESCE(vf.form_text, '') IN ({placeholders})
          )
        ORDER BY match_rank, vi.id
        LIMIT 4
        """,
        [
            *candidates,
            *candidates,
            exam_system_id,
            level_id,
            *candidates,
            *candidates,
            *candidates,
        ],
    ).fetchall()
    if not rows:
        return None
    meanings = []
    for row in rows:
        meaning = clean_word_meaning_for_display(row["meaning_zh"])
        if meaning and meaning not in meanings:
            meanings.append(meaning)
    best = rows[0]
    return {
        "selected_text": selected_text,
        "lemma": best["lemma"] or best["word"],
        "part_of_speech": best["part_of_speech"] or "",
        "meaning_zh": "；".join(meanings),
        "context_meaning_zh": "",
        "note_zh": "",
        "matched_by_morphology": best["word"].casefold() != selected_text.casefold(),
        "source": "local_dictionary",
        "source_label": "AIeyu 已审核词库",
        "vocabulary_item_id": int(best["id"]),
        "cached": False,
        "requires_ai_confirmation": False,
    }


def deepseek_selection_translation(selected_text: str, context: str) -> dict[str, Any]:
    messages = [
        {
            "role": "system",
            "content": (
                "你是俄汉词典编辑。根据俄语词或短语及上下文返回严格 JSON，不要使用 Markdown。"
                "字段必须为 lemma、part_of_speech、meaning_zh、context_meaning_zh、note_zh。"
                "释义使用简洁准确的中文；不确定时如实说明，不罗列无关义项；"
                "note_zh 最多一句，只写必要的词形或搭配提示。"
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {"selected_text": selected_text, "context": context},
                ensure_ascii=False,
            ),
        },
    ]
    parsed = parse_assistant_json(assistant_text_from_response(deepseek_chat(messages)))
    meaning = re.sub(r"\s+", " ", str(parsed.get("meaning_zh") or "").strip())
    context_meaning = re.sub(r"\s+", " ", str(parsed.get("context_meaning_zh") or "").strip())
    if not meaning and not context_meaning:
        raise ValueError("翻译服务没有返回有效释义。")
    return {
        "selected_text": selected_text,
        "lemma": re.sub(r"\s+", " ", str(parsed.get("lemma") or selected_text).strip())[:100],
        "part_of_speech": re.sub(r"\s+", " ", str(parsed.get("part_of_speech") or "").strip())[:60],
        "meaning_zh": meaning[:500],
        "context_meaning_zh": context_meaning[:500],
        "note_zh": re.sub(r"\s+", " ", str(parsed.get("note_zh") or "").strip())[:300],
        "source": "deepseek",
        "source_label": "AI 语境翻译",
        "vocabulary_item_id": None,
        "cached": False,
        "requires_ai_confirmation": False,
    }


def api_translate_selection(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = normalize_user_id(payload.get("user_id"))
    selected_text = clean_selection_text(payload.get("selected_text"))
    context = clean_selection_context(payload.get("context"), selected_text)
    exam_system_code = str(payload.get("exam_system") or "TEM8_RU")
    level_code = str(payload.get("level") or "TEM8")
    allow_ai = payload.get("allow_ai") is True
    context_hash = hashlib.sha256(context.casefold().encode("utf-8")).hexdigest()

    with db() as conn:
        ensure_user_exists(conn, user_id)
        exam_system_id, level_id = fetch_ids(conn, exam_system_code, level_code)
        local_result = local_selection_translation(conn, selected_text, exam_system_id, level_id)
        if local_result:
            return local_result
        cached = conn.execute(
            """
            SELECT id, result_json
            FROM selection_translation_cache
            WHERE selected_text = ? AND context_hash = ?
            """,
            (selected_text.casefold(), context_hash),
        ).fetchone()
        if cached:
            conn.execute(
                """
                UPDATE selection_translation_cache
                SET hit_count = hit_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (cached["id"],),
            )
            result = json.loads(cached["result_json"])
            result["cached"] = True
            return result

    if not allow_ai:
        return {
            "selected_text": selected_text,
            "source": "not_found",
            "source_label": "本地词库未收录",
            "requires_ai_confirmation": True,
            "ai_notice": "将选中内容和所在句子发送给 DeepSeek 进行语境翻译。",
        }

    result = deepseek_selection_translation(selected_text, context)
    with db() as conn:
        conn.execute(
            """
            INSERT INTO selection_translation_cache (
              selected_text, context_hash, result_json, provider
            )
            VALUES (?, ?, ?, 'deepseek')
            ON CONFLICT(selected_text, context_hash) DO UPDATE SET
              result_json = excluded.result_json,
              updated_at = CURRENT_TIMESTAMP
            """,
            (selected_text.casefold(), context_hash, json.dumps(result, ensure_ascii=False)),
        )
    return result


def generate_explanation_for_session(quiz_session_id: int) -> dict[str, Any]:
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    with db() as conn:
        report = grading_report_for_session(conn, quiz_session_id)
        if not report["wrong_questions"]:
            return {
                "quiz_session_id": quiz_session_id,
                "thread_id": None,
                "assistant_text": "这次没有错题，暂时不需要生成错题讲解。可以继续生成新练习或做一次薄弱点专项。",
                "question_explanations": [],
                "study_advice_zh": "",
            }
        user_payload = build_tutor_payload(report)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False, indent=2)},
    ]
    response = deepseek_chat(messages)
    assistant_text = assistant_text_from_response(response)
    assistant_json = parse_assistant_json(assistant_text)
    question_explanations = assistant_json.get("question_explanations", [])
    if not isinstance(question_explanations, list):
        question_explanations = []
    study_advice_zh = assistant_json.get("study_advice_zh", "")
    if not isinstance(study_advice_zh, str):
        study_advice_zh = ""

    with db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO ai_tutor_threads (user_id, quiz_session_id, title)
            VALUES (?, ?, ?)
            """,
            (
                report["user_id"] or DEFAULT_USER_ID,
                quiz_session_id,
                f"TEM8 student explanation {datetime.now().isoformat(timespec='minutes')}",
            ),
        )
        thread_id = int(cursor.lastrowid)
        conn.execute(
            "INSERT INTO ai_tutor_messages (thread_id, role, content) VALUES (?, 'system', ?)",
            (thread_id, system_prompt),
        )
        conn.execute(
            "INSERT INTO ai_tutor_messages (thread_id, role, content) VALUES (?, 'user', ?)",
            (thread_id, json.dumps(user_payload, ensure_ascii=False, indent=2)),
        )
        conn.execute(
            """
            INSERT INTO ai_tutor_messages (thread_id, role, content, rag_references_json)
            VALUES (?, 'assistant', ?, ?)
            """,
            (
                thread_id,
                assistant_text,
                json.dumps({"provider": "deepseek", "raw_response": response}, ensure_ascii=False),
            ),
        )
        conn.commit()
    return {
        "quiz_session_id": quiz_session_id,
        "thread_id": thread_id,
        "assistant_text": assistant_text,
        "question_explanations": question_explanations,
        "study_advice_zh": study_advice_zh or assistant_text,
    }


def api_generate_explanation(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("confirm_external_send"):
        raise ValueError("请先确认允许把本次错题数据发送到 DeepSeek。")
    user_id = normalize_user_id(payload.get("user_id"))
    quiz_session_id = int(payload["quiz_session_id"])
    with db() as conn:
        session = conn.execute(
            "SELECT user_id FROM quiz_sessions WHERE id = ?",
            (quiz_session_id,),
        ).fetchone()
        if session is None:
            raise ValueError(f"没有找到测试记录 {quiz_session_id}。")
        if session["user_id"] is not None and int(session["user_id"]) != user_id:
            raise ValueError("这个测试记录不属于当前学生。")
    return generate_explanation_for_session(quiz_session_id)


def api_followup(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("confirm_external_send"):
        raise ValueError("请先确认允许把本对话上下文发送到 DeepSeek。")
    thread_id = int(payload["thread_id"])
    user_id = normalize_user_id(payload.get("user_id"))
    user_message = str(payload.get("message") or "").strip()
    if not user_message:
        raise ValueError("追问内容不能为空。")

    with db() as conn:
        ensure_user_exists(conn, user_id)
        thread = conn.execute(
            "SELECT user_id FROM ai_tutor_threads WHERE id = ?",
            (thread_id,),
        ).fetchone()
        if thread is None:
            raise ValueError(f"没有找到 AI 对话线程 {thread_id}。")
        if thread["user_id"] is not None and int(thread["user_id"]) != user_id:
            raise ValueError("这个 AI 对话不属于当前学生。")
        rows = conn.execute(
            """
            SELECT role, content
            FROM ai_tutor_messages
            WHERE thread_id = ?
            ORDER BY id
            """,
            (thread_id,),
        ).fetchall()
        if not rows:
            raise ValueError(f"没有找到 AI 对话线程 {thread_id}。")
        messages = [{"role": row["role"], "content": row["content"]} for row in rows]

    messages.append({"role": "user", "content": user_message})
    response = deepseek_chat(messages)
    assistant_text = assistant_text_from_response(response)

    with db() as conn:
        conn.execute(
            "INSERT INTO ai_tutor_messages (thread_id, role, content) VALUES (?, 'user', ?)",
            (thread_id, user_message),
        )
        conn.execute(
            """
            INSERT INTO ai_tutor_messages (thread_id, role, content, rag_references_json)
            VALUES (?, 'assistant', ?, ?)
            """,
            (
                thread_id,
                assistant_text,
                json.dumps({"provider": "deepseek", "raw_response": response}, ensure_ascii=False),
            ),
        )
        conn.execute("UPDATE ai_tutor_threads SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (thread_id,))
        conn.commit()
    return {"thread_id": thread_id, "assistant_text": assistant_text}


def json_response(
    handler: BaseHTTPRequestHandler,
    status: HTTPStatus,
    payload: dict[str, Any],
    extra_headers: dict[str, str] | None = None,
) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    for key, value in (extra_headers or {}).items():
        handler.send_header(key, value)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class StudentAppHandler(BaseHTTPRequestHandler):
    server_version = "AIeyuStudentApp/0.1"

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            if parsed.path == "/api/health":
                health = api_health()
                json_response(self, HTTPStatus.OK if health["ready"] else HTTPStatus.SERVICE_UNAVAILABLE, health)
                return
            if parsed.path == "/api/status":
                json_response(self, HTTPStatus.OK, api_status(query.get("exam_system", ["TEM8_RU"])[0], query.get("level", ["TEM8"])[0]))
                return
            if parsed.path == "/api/auth/status":
                json_response(self, HTTPStatus.OK, api_auth_status(self))
                return
            if parsed.path == "/api/users":
                user_id = authenticated_user_id(self)
                json_response(self, HTTPStatus.OK, api_users(user_id))
                return
            if parsed.path == "/api/profile":
                json_response(self, HTTPStatus.OK, api_profile(authenticated_user_id(self), query.get("exam_system", ["TEM8_RU"])[0], query.get("level", ["TEM8"])[0]))
                return
            if parsed.path == "/api/study-center":
                json_response(self, HTTPStatus.OK, api_study_center(authenticated_user_id(self), query.get("exam_system", ["TEM8_RU"])[0], query.get("level", ["TEM8"])[0]))
                return
            if parsed.path == "/api/wrongbook":
                limit = int(query.get("limit", ["80"])[0])
                json_response(self, HTTPStatus.OK, api_wrongbook(authenticated_user_id(self), limit, query.get("exam_system", ["TEM8_RU"])[0], query.get("level", ["TEM8"])[0]))
                return
            if parsed.path == "/api/words/status":
                json_response(
                    self,
                    HTTPStatus.OK,
                    api_word_status(
                        authenticated_user_id(self),
                        query.get("exam_system", ["TEM8_RU"])[0],
                        query.get("level", ["TEM8"])[0],
                    ),
                )
                return
            if parsed.path == "/api/words/review-pool":
                limit = int(query.get("limit", ["80"])[0])
                json_response(
                    self,
                    HTTPStatus.OK,
                    api_word_review_pool(
                        authenticated_user_id(self),
                        limit,
                        query.get("exam_system", ["TEM8_RU"])[0],
                        query.get("level", ["TEM8"])[0],
                    ),
                )
                return
            if parsed.path == "/api/thread":
                thread_id = int(query.get("id", ["1"])[0])
                json_response(self, HTTPStatus.OK, api_thread(thread_id, authenticated_user_id(self)))
                return
            self.serve_static(parsed.path)
        except PermissionError as exc:
            json_response(self, HTTPStatus.UNAUTHORIZED, {"error": str(exc)})
        except Exception as exc:
            json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if self.path == "/api/auth/register":
                result, cookie = api_register(payload)
                json_response(self, HTTPStatus.OK, result, {"Set-Cookie": cookie})
                return
            if self.path == "/api/auth/login":
                result, cookie = api_login(payload)
                json_response(self, HTTPStatus.OK, result, {"Set-Cookie": cookie})
                return
            if self.path == "/api/auth/logout":
                result, cookie = api_logout(self)
                json_response(self, HTTPStatus.OK, result, {"Set-Cookie": cookie})
                return
            if self.path == "/api/quiz":
                payload["user_id"] = authenticated_user_id(self)
                json_response(self, HTTPStatus.OK, api_generate_quiz(payload))
                return
            if self.path == "/api/grade":
                payload["user_id"] = authenticated_user_id(self)
                json_response(self, HTTPStatus.OK, api_grade(payload))
                return
            if self.path == "/api/words/session":
                payload["user_id"] = authenticated_user_id(self)
                json_response(self, HTTPStatus.OK, api_word_session(payload))
                return
            if self.path == "/api/words/review":
                payload["user_id"] = authenticated_user_id(self)
                json_response(self, HTTPStatus.OK, api_word_review(payload))
                return
            if self.path == "/api/words/feedback":
                payload["user_id"] = authenticated_user_id(self)
                json_response(self, HTTPStatus.OK, api_word_feedback(payload))
                return
            if self.path == "/api/wrongbook/item":
                payload["user_id"] = authenticated_user_id(self)
                json_response(self, HTTPStatus.OK, api_update_wrongbook_item(payload))
                return
            if self.path == "/api/feedback":
                payload["user_id"] = authenticated_user_id(self)
                json_response(self, HTTPStatus.OK, api_product_feedback(payload))
                return
            if self.path == "/api/translate-selection":
                payload["user_id"] = authenticated_user_id(self)
                json_response(self, HTTPStatus.OK, api_translate_selection(payload))
                return
            if self.path == "/api/explain":
                payload["user_id"] = authenticated_user_id(self)
                json_response(self, HTTPStatus.OK, api_generate_explanation(payload))
                return
            if self.path == "/api/followup":
                payload["user_id"] = authenticated_user_id(self)
                json_response(self, HTTPStatus.OK, api_followup(payload))
                return
            json_response(self, HTTPStatus.NOT_FOUND, {"error": "Not found"})
        except PermissionError as exc:
            json_response(self, HTTPStatus.UNAUTHORIZED, {"error": str(exc)})
        except Exception as exc:
            json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def serve_static(self, path: str) -> None:
        relative = "index.html" if path in ("", "/") else path.lstrip("/")
        target = (STATIC_DIR / relative).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        body = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Serve the local AIeyu student web prototype.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), StudentAppHandler)
    print(f"AIeyu student app: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
