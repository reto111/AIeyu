from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from knowledge_base import connect, ensure_knowledge_base_tables, fetch_tem8_ids
from search_knowledge_chunks import search_chunks


ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "prompts" / "generation" / "tem8_choice_question_generator.md"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "processed" / "ai_question_generation"
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"
OPTION_KEYS = ["A", "B", "C", "D"]
SIMILARITY_THRESHOLD = 0.86


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def ensure_generation_reference_table(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS question_generation_references (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          question_id INTEGER NOT NULL,
          knowledge_chunk_id INTEGER NOT NULL,
          role TEXT NOT NULL DEFAULT 'source_context' CHECK (role IN ('source_context', 'style_reference', 'similarity_reference')),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
          FOREIGN KEY (knowledge_chunk_id) REFERENCES knowledge_chunks(id),
          UNIQUE (question_id, knowledge_chunk_id, role)
        );

        CREATE INDEX IF NOT EXISTS idx_question_generation_references_question
          ON question_generation_references (question_id, role);
        """
    )


def fetch_one_id(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> int:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise ValueError(f"Missing database row for query: {sql} {params}")
    return int(row[0])


def truncate_chunk_body(body: str, max_chars: int) -> str:
    body = body.strip()
    if len(body) <= max_chars:
        return body
    return body[:max_chars].rstrip() + "\n...[truncated]"


def build_prompt_package(
    *,
    question_type: str,
    knowledge_point: str,
    query: str,
    count: int,
    difficulty: int,
    chunks_limit: int,
    max_chunk_chars: int,
) -> dict[str, Any]:
    chunks = search_chunks(
        query=query,
        question_type=question_type,
        knowledge_point=knowledge_point,
        limit=chunks_limit,
        reviewed_only=True,
    )
    if not chunks:
        raise ValueError("没有检索到可用知识块，请换关键词或先导入资料。")

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    return {
        "system_prompt": prompt,
        "user_payload": {
            "generation_request": {
                "exam_system": "TEM8_RU",
                "level": "TEM8",
                "question_type": question_type,
                "knowledge_point": knowledge_point,
                "query": query,
                "count": count,
                "difficulty": difficulty,
                "review_policy": "ai_generated_questions_must_be_needs_review_before_practice",
            },
            "retrieved_chunks": [
                {
                    "id": chunk["id"],
                    "title": chunk["title"],
                    "knowledge_point_code": chunk["knowledge_point_code"],
                    "source_locator": chunk["source_locator"],
                    "body": truncate_chunk_body(chunk["body"], max_chunk_chars),
                }
                for chunk in chunks
            ],
        },
    }


def chat_completion(
    *,
    api_key: str,
    base_url: str,
    model: str,
    prompt_package: dict[str, Any],
    max_tokens: int,
    timeout: int,
) -> dict[str, Any]:
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt_package["system_prompt"]},
            {
                "role": "user",
                "content": json.dumps(prompt_package["user_payload"], ensure_ascii=False, indent=2),
            },
        ],
        "thinking": {"type": "disabled"},
        "stream": False,
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API error {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"DeepSeek API connection failed: {exc}") from exc


def assistant_content(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        raise ValueError("DeepSeek response has no choices.")
    content = (choices[0].get("message") or {}).get("content")
    if not content:
        raise ValueError("DeepSeek response has no assistant content.")
    return str(content)


def parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, flags=re.DOTALL)
    if fenced:
        stripped = fenced.group(1).strip()
    return json.loads(stripped)


def validate_questions(payload: dict[str, Any], expected_count: int) -> list[dict[str, Any]]:
    questions = payload.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("AI response must contain a non-empty questions list.")
    if len(questions) != expected_count:
        raise ValueError(f"AI response returned {len(questions)} questions, expected {expected_count}.")

    validated: list[dict[str, Any]] = []
    for index, question in enumerate(questions, start=1):
        stem = str(question.get("stem") or "").strip()
        correct_answer = str(question.get("correct_answer") or "").strip().upper()
        explanation = str(question.get("explanation_zh") or "").strip()
        options = question.get("options")
        if not stem:
            raise ValueError(f"Question {index} missing stem.")
        if correct_answer not in OPTION_KEYS:
            raise ValueError(f"Question {index} invalid correct_answer: {correct_answer}")
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError(f"Question {index} must have exactly 4 options.")
        keys = [str(option.get("key") or "").strip().upper() for option in options]
        if sorted(keys) != OPTION_KEYS:
            raise ValueError(f"Question {index} option keys must be A/B/C/D.")
        if not explanation:
            raise ValueError(f"Question {index} missing explanation_zh.")
        validated.append(question)
    return validated


def collect_knowledge_point_codes(questions: list[dict[str, Any]], default_code: str) -> list[str]:
    codes = {default_code}
    for question in questions:
        for code in question.get("knowledge_point_codes", []) or []:
            if code:
                codes.add(str(code))
    return sorted(codes)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def similarity_ratio(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_text(left), normalize_text(right)).ratio()


def detect_similarity_risks(
    conn: sqlite3.Connection,
    questions: list[dict[str, Any]],
    prompt_package: dict[str, Any],
    threshold: float,
) -> list[str]:
    risks: list[str] = []
    existing_questions = conn.execute(
        """
        SELECT id, stem
        FROM questions
        WHERE review_status IN ('needs_review', 'approved')
        """
    ).fetchall()
    chunk_bodies = [
        str(chunk.get("body") or "")
        for chunk in prompt_package["user_payload"]["retrieved_chunks"]
    ]

    for index, question in enumerate(questions, start=1):
        stem = str(question.get("stem") or "")
        normalized_stem = normalize_text(stem)
        if len(normalized_stem) >= 20:
            for chunk_body in chunk_bodies:
                if normalized_stem in normalize_text(chunk_body):
                    risks.append(f"Question {index} stem appears inside a retrieved knowledge chunk.")
                    break

        for row in existing_questions:
            ratio = similarity_ratio(stem, str(row["stem"] or ""))
            if ratio >= threshold:
                risks.append(
                    f"Question {index} is too similar to existing question {row['id']} "
                    f"(ratio={ratio:.2f})."
                )
                break

    return risks


def insert_generated_questions(
    conn: sqlite3.Connection,
    questions: list[dict[str, Any]],
    prompt_package: dict[str, Any],
    question_type: str,
    knowledge_point: str,
) -> list[int]:
    ensure_knowledge_base_tables(conn)
    ensure_generation_reference_table(conn)
    exam_system_id, level_id = fetch_tem8_ids(conn)
    similarity_risks = detect_similarity_risks(conn, questions, prompt_package, SIMILARITY_THRESHOLD)
    if similarity_risks:
        raise ValueError("AI generated questions failed similarity checks: " + "; ".join(similarity_risks))

    question_type_id = fetch_one_id(conn, "SELECT id FROM question_types WHERE code = ?", (question_type,))
    chunk_ids = [int(chunk["id"]) for chunk in prompt_package["user_payload"]["retrieved_chunks"]]
    point_codes = collect_knowledge_point_codes(questions, knowledge_point)
    placeholders = ", ".join("?" for _ in point_codes)
    knowledge_point_ids = [
        int(row[0])
        for row in conn.execute(
            f"""
            SELECT id
            FROM knowledge_points
            WHERE exam_system_id = ? AND code IN ({placeholders})
            """,
            (exam_system_id, *point_codes),
        ).fetchall()
    ]
    if not knowledge_point_ids:
        raise ValueError(f"No valid knowledge points found for generated questions: {point_codes}")
    inserted_ids: list[int] = []

    for index, question in enumerate(questions, start=1):
        raw_text = {
            "generator": "deepseek",
            "prompt_version": "tem8_choice_question_generator_v1",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_chunk_ids": chunk_ids,
            "source_basis_zh": question.get("source_basis_zh"),
        }
        cursor = conn.execute(
            """
            INSERT INTO questions (
              exam_system_id, level_id, question_type_id, stem, correct_answer,
              explanation_zh, difficulty, review_status, generation_status, raw_text,
              source_usage, content_origin, source_label, requires_source_label,
              similarity_review_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'needs_review', 'ai_draft', ?, 'practice',
                    'ai_generated', 'AI 生成题草稿', 0, 'not_checked')
            """,
            (
                exam_system_id,
                level_id,
                question_type_id,
                question["stem"].strip(),
                question["correct_answer"].strip().upper(),
                question["explanation_zh"].strip(),
                int(question.get("difficulty") or 3),
                json.dumps(raw_text, ensure_ascii=False),
            ),
        )
        question_id = int(cursor.lastrowid)
        inserted_ids.append(question_id)

        for sort_order, option in enumerate(question["options"]):
            conn.execute(
                """
                INSERT INTO question_options (question_id, option_key, option_text, sort_order)
                VALUES (?, ?, ?, ?)
                """,
                (question_id, option["key"].strip().upper(), option["text"].strip(), sort_order),
            )

        for knowledge_point_id in knowledge_point_ids:
            conn.execute(
                """
                INSERT OR IGNORE INTO question_knowledge_points (question_id, knowledge_point_id)
                VALUES (?, ?)
                """,
                (question_id, knowledge_point_id),
            )
        for chunk_id in chunk_ids:
            conn.execute(
                """
                INSERT OR IGNORE INTO question_generation_references (question_id, knowledge_chunk_id)
                VALUES (?, ?)
                """,
                (question_id, chunk_id),
            )
        conn.execute(
            """
            INSERT INTO question_review_logs (
              question_id, review_decision, review_notes, knowledge_point_codes, reviewer
            )
            VALUES (?, 'needs_review', ?, ?, 'ai_generator')
            """,
            (
                question_id,
                f"AI generated draft batch item {index}; must be manually reviewed before use.",
                ", ".join(point_codes),
            ),
        )

    conn.commit()
    return inserted_ids


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="Generate AI TEM8 choice question drafts with knowledge chunks.")
    parser.add_argument("--question-type", default="culture_choice")
    parser.add_argument("--knowledge-point", default="culture")
    parser.add_argument("--query", default="卫国战争")
    parser.add_argument("--count", type=int, default=2)
    parser.add_argument("--difficulty", type=int, default=3)
    parser.add_argument("--chunks-limit", type=int, default=4)
    parser.add_argument("--max-chunk-chars", type=int, default=1400)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--model", default=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--max-tokens", type=int, default=2400)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--confirm-external-send", action="store_true")
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args()

    prompt_package = build_prompt_package(
        question_type=args.question_type,
        knowledge_point=args.knowledge_point,
        query=args.query,
        count=args.count,
        difficulty=args.difficulty,
        chunks_limit=args.chunks_limit,
        max_chunk_chars=args.max_chunk_chars,
    )
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prompt_path = args.output_dir / f"generation_prompt_{stamp}.json"
    write_json(prompt_path, prompt_package)

    if not args.confirm_external_send:
        print(
            json.dumps(
                {
                    "status": "dry_run",
                    "message": "已生成提示词预览；未调用 DeepSeek，未写入题库。",
                    "prompt_path": str(prompt_path),
                    "retrieved_chunk_ids": [
                        chunk["id"] for chunk in prompt_package["user_payload"]["retrieved_chunks"]
                    ],
                    "next_step": "确认允许发送知识块到 DeepSeek 后，重新运行并添加 --confirm-external-send --persist。",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key or api_key == "your_deepseek_api_key_here":
        raise SystemExit("Missing DEEPSEEK_API_KEY.")

    response = chat_completion(
        api_key=api_key,
        base_url=args.base_url,
        model=args.model,
        prompt_package=prompt_package,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
    )
    assistant_text = assistant_content(response)
    generated_payload = parse_json_object(assistant_text)
    questions = validate_questions(generated_payload, args.count)

    inserted_ids: list[int] = []
    if args.persist:
        with connect() as conn:
            inserted_ids = insert_generated_questions(
                conn,
                questions,
                prompt_package,
                args.question_type,
                args.knowledge_point,
            )

    output_path = args.output_dir / f"generation_result_{stamp}.json"
    write_json(
        output_path,
        {
            "prompt_path": str(prompt_path),
            "model": args.model,
            "inserted_question_ids": inserted_ids,
            "assistant_payload": generated_payload,
            "raw_response": response,
        },
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "output_path": str(output_path),
                "inserted_question_ids": inserted_ids,
                "review_status": "needs_review" if inserted_ids else "not_persisted",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
