from __future__ import annotations

import argparse
import json
import mimetypes
import os
import random
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
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


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    ensure_adaptive_tables(conn)
    ensure_default_user(conn)
    return conn


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


def api_status() -> dict[str, Any]:
    with db() as conn:
        by_type = [
            {
                "code": row["code"],
                "name": QUESTION_TYPE_NAMES.get(row["code"], row["name_zh"]),
                "count": row["count"],
            }
            for row in conn.execute(
                """
                SELECT qt.code, qt.name_zh, COUNT(*) AS count
                FROM questions q
                JOIN question_types qt ON qt.id = q.question_type_id
                WHERE q.review_status = 'approved' AND q.source_usage = 'practice'
                GROUP BY qt.code, qt.name_zh
                ORDER BY qt.code
                """
            ).fetchall()
        ]
        years = [
            {"year": row["source_year"], "count": row["count"]}
            for row in conn.execute(
                """
                SELECT source_year, COUNT(*) AS count
                FROM questions
                WHERE review_status = 'approved' AND source_usage = 'practice'
                GROUP BY source_year
                ORDER BY source_year
                """
            ).fetchall()
        ]
        latest_thread = conn.execute(
            """
            SELECT id, quiz_session_id, title, updated_at
            FROM ai_tutor_threads
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
    return {
        "question_count": sum(item["count"] for item in by_type),
        "question_types": by_type,
        "years": years,
        "latest_thread": dict(latest_thread) if latest_thread else None,
        "deepseek_configured": bool(os.environ.get("DEEPSEEK_API_KEY")),
    }


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
        candidates = sorted(
            grouped.get(code, []),
            key=lambda row: adaptive_selection_score(exposures.get(int(row["id"])), rng),
            reverse=True,
        )
        selected.extend(candidates[:target])
        remaining_pool.extend(candidates[target:])

    if len(selected) < count:
        selected_ids = {int(row["id"]) for row in selected}
        fallback = sorted(
            [row for row in remaining_pool if int(row["id"]) not in selected_ids],
            key=lambda row: adaptive_selection_score(exposures.get(int(row["id"])), rng),
            reverse=True,
        )
        selected.extend(fallback[: count - len(selected)])

    return selected[:count]


def api_generate_quiz(payload: dict[str, Any]) -> dict[str, Any]:
    count = max(1, min(int(payload.get("count") or 10), 50))
    mode = str(payload.get("mode") or "random")
    question_types = [str(item) for item in payload.get("question_types", []) if item]
    if mode == "diagnostic" and not question_types:
        question_types = DIAGNOSTIC_QUESTION_TYPES
    if not question_types:
        question_types = DEFAULT_RANDOM_QUESTION_TYPES
    years = [int(item) for item in payload.get("years", []) if item]
    seed = payload.get("seed")
    rng = random.Random(seed)

    params: list[Any] = []
    filters = ["q.review_status = 'approved'", "q.source_usage = 'practice'"]
    if question_types:
        placeholders = ", ".join("?" for _ in question_types)
        filters.append(f"qt.code IN ({placeholders})")
        params.extend(question_types)
    if years:
        placeholders = ", ".join("?" for _ in years)
        filters.append(f"q.source_year IN ({placeholders})")
        params.extend(years)

    with db() as conn:
        rows = conn.execute(
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
        if len(rows) < count:
            raise ValueError(f"当前条件下只有 {len(rows)} 道题，无法生成 {count} 道。")
        exposures = exposure_rows(conn, DEFAULT_USER_ID, [int(row["id"]) for row in rows])
        if mode == "diagnostic":
            selected = select_balanced_by_type(rows, count, question_types, exposures, rng)
        else:
            selected = sorted(
                rows,
                key=lambda row: adaptive_selection_score(exposures.get(int(row["id"])), rng),
                reverse=True,
            )
        questions = [
            public_question(conn, row, index)
            for index, row in enumerate(selected[:count], start=1)
        ]
    return {
        "exam_system": "TEM8_RU",
        "level": "TEM8",
        "mode": mode,
        "count": len(questions),
        "questions": questions,
    }


def api_profile() -> dict[str, Any]:
    with db() as conn:
        return recalculate_profile(conn, DEFAULT_USER_ID)


def fetch_ids(conn: sqlite3.Connection) -> tuple[int, int]:
    exam_system_id = int(conn.execute("SELECT id FROM exam_systems WHERE code = 'TEM8_RU'").fetchone()[0])
    level_id = int(
        conn.execute(
            "SELECT id FROM exam_levels WHERE exam_system_id = ? AND code = 'TEM8'",
            (exam_system_id,),
        ).fetchone()[0]
    )
    return exam_system_id, level_id


def summary_for_code(code: str, attempted: int, wrong: int) -> str:
    name = KNOWLEDGE_NAMES.get(code, code)
    if wrong == 0:
        return f"{name}: 本次全部答对，保持节奏。"
    return f"{name}: 本次 {attempted} 题中错 {wrong} 题，建议先回看错题，再做同类巩固。"


def api_grade(payload: dict[str, Any]) -> dict[str, Any]:
    submitted_answers = payload.get("answers") or []
    if not submitted_answers:
        raise ValueError("还没有收到答案。")

    with db() as conn:
        user_id = DEFAULT_USER_ID
        exam_system_id, level_id = fetch_ids(conn)
        cursor = conn.execute(
            """
            INSERT INTO quiz_sessions (
              user_id, exam_system_id, level_id, title, mode, status, total_questions
            )
            VALUES (?, ?, ?, ?, 'random', 'submitted', ?)
            """,
            (
                user_id,
                exam_system_id,
                level_id,
                payload.get("title") or "TEM8 student practice",
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
        result["profile"] = recalculate_profile(conn, DEFAULT_USER_ID)
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
        SELECT id, total_questions, correct_count, accuracy, submitted_at
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


def api_thread(thread_id: int) -> dict[str, Any]:
    with db() as conn:
        thread = conn.execute(
            """
            SELECT id, quiz_session_id, title, created_at, updated_at
            FROM ai_tutor_threads
            WHERE id = ?
            """,
            (thread_id,),
        ).fetchone()
        if thread is None:
            raise ValueError(f"没有找到 AI 对话线程 {thread_id}。")
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
            INSERT INTO ai_tutor_threads (quiz_session_id, title)
            VALUES (?, ?)
            """,
            (quiz_session_id, f"TEM8 student explanation {datetime.now().isoformat(timespec='minutes')}"),
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
    return generate_explanation_for_session(int(payload["quiz_session_id"]))


def api_followup(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("confirm_external_send"):
        raise ValueError("请先确认允许把本对话上下文发送到 DeepSeek。")
    thread_id = int(payload["thread_id"])
    user_message = str(payload.get("message") or "").strip()
    if not user_message:
        raise ValueError("追问内容不能为空。")

    with db() as conn:
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


def json_response(handler: BaseHTTPRequestHandler, status: HTTPStatus, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class StudentAppHandler(BaseHTTPRequestHandler):
    server_version = "AIeyuStudentApp/0.1"

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/api/status":
                json_response(self, HTTPStatus.OK, api_status())
                return
            if parsed.path == "/api/profile":
                json_response(self, HTTPStatus.OK, api_profile())
                return
            if parsed.path == "/api/thread":
                query = parse_qs(parsed.query)
                thread_id = int(query.get("id", ["1"])[0])
                json_response(self, HTTPStatus.OK, api_thread(thread_id))
                return
            self.serve_static(parsed.path)
        except Exception as exc:
            json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if self.path == "/api/quiz":
                json_response(self, HTTPStatus.OK, api_generate_quiz(payload))
                return
            if self.path == "/api/grade":
                json_response(self, HTTPStatus.OK, api_grade(payload))
                return
            if self.path == "/api/explain":
                json_response(self, HTTPStatus.OK, api_generate_explanation(payload))
                return
            if self.path == "/api/followup":
                json_response(self, HTTPStatus.OK, api_followup(payload))
                return
            json_response(self, HTTPStatus.NOT_FOUND, {"error": "Not found"})
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
