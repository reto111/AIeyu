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
AI_DRAFT_SIMILARITY_THRESHOLD = 0.74
BATCH_SIMILARITY_THRESHOLD = 0.78


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


def years_in_text(text: str) -> set[str]:
    return set(re.findall(r"(?:1[0-9]{3}|20[0-9]{2})", text))


def culture_key_terms(text: str) -> set[str]:
    terms = [
        "莫斯科",
        "首都",
        "克里姆林宫",
        "红场",
        "苏联",
        "俄罗斯",
        "总统",
        "官邸",
        "炮王",
        "钟王",
        "莫斯科大学",
        "圣彼得堡",
        "成立",
        "迁都",
        "联邦",
    ]
    return {term for term in terms if term in text}


def is_same_culture_signature(left: str, right: str) -> bool:
    left_years = years_in_text(left)
    right_years = years_in_text(right)
    shared_years = left_years & right_years
    shared_terms = culture_key_terms(left) & culture_key_terms(right)
    return len(shared_years) >= 2 and len(shared_terms) >= 2


def question_payload_text(question: dict[str, Any]) -> str:
    option_texts = [
        str(option.get("text") or "")
        for option in question.get("options", []) or []
        if isinstance(option, dict)
    ]
    return "\n".join(
        [
            str(question.get("stem") or ""),
            *option_texts,
            str(question.get("explanation_zh") or ""),
        ]
    )


def existing_question_payloads(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
          q.id,
          q.stem,
          q.explanation_zh,
          q.generation_status,
          q.review_status,
          qt.code AS question_type
        FROM questions q
        JOIN question_types qt ON qt.id = q.question_type_id
        WHERE q.review_status IN ('needs_review', 'approved')
        """
    ).fetchall()
    option_rows = conn.execute(
        """
        SELECT question_id, option_key, option_text
        FROM question_options
        ORDER BY question_id, option_key
        """
    ).fetchall()
    options_by_question: dict[int, list[str]] = {}
    for row in option_rows:
        options_by_question.setdefault(int(row["question_id"]), []).append(str(row["option_text"] or ""))

    payloads: list[dict[str, Any]] = []
    for row in rows:
        question_id = int(row["id"])
        payloads.append(
            {
                "id": question_id,
                "question_type": row["question_type"],
                "generation_status": row["generation_status"],
                "review_status": row["review_status"],
                "text": "\n".join(
                    [
                        str(row["stem"] or ""),
                        *options_by_question.get(question_id, []),
                        str(row["explanation_zh"] or ""),
                    ]
                ),
                "stem": str(row["stem"] or ""),
            }
        )
    return payloads


def detect_batch_similarity_risks(questions: list[dict[str, Any]]) -> list[str]:
    risks: list[str] = []
    for left_index, left_question in enumerate(questions, start=1):
        for right_index, right_question in enumerate(questions[left_index:], start=left_index + 1):
            ratio = similarity_ratio(
                question_payload_text(left_question),
                question_payload_text(right_question),
            )
            if ratio >= BATCH_SIMILARITY_THRESHOLD:
                risks.append(
                    f"Question {left_index} is too similar to generated question {right_index} "
                    f"(payload_ratio={ratio:.2f})."
                )
    return risks


def detect_culture_difficulty_risks(
    questions: list[dict[str, Any]],
    question_type: str,
    requested_difficulty: int,
) -> list[str]:
    if question_type != "culture_choice" or requested_difficulty < 4:
        return []

    risks: list[str] = []
    low_depth_patterns = [
        "名称是什么",
        "叫什么",
        "位于哪里",
        "哪一项是正确的",
        "哪一项正确",
        "下列关于",
    ]
    depth_markers = [
        "时间",
        "时期",
        "背景",
        "关系",
        "原因",
        "制度",
        "事件",
        "成立",
        "成为",
        "混淆",
        "对应",
        "节点",
        "历史",
        "综合",
        "组合",
        "判断",
        "描述",
        "特征",
        "流向",
        "水量",
        "别称",
        "分布",
        "产地",
        "资源",
    ]
    for index, question in enumerate(questions, start=1):
        stem = str(question.get("stem") or "")
        options_text = " ".join(
            str(option.get("text") or "")
            for option in question.get("options", []) or []
            if isinstance(option, dict)
        )
        text = stem + " " + options_text
        year_count = len(years_in_text(text))
        stem_marker_count = sum(1 for marker in depth_markers if marker in stem)
        has_low_depth_pattern = any(pattern in stem for pattern in low_depth_patterns)
        if has_low_depth_pattern and year_count < 2 and stem_marker_count < 2:
            risks.append(
                f"Question {index} may be too shallow for culture difficulty>=4 "
                "(single fact/name/location style)."
            )
    return risks


def detect_similarity_risks(
    conn: sqlite3.Connection,
    questions: list[dict[str, Any]],
    prompt_package: dict[str, Any],
    threshold: float,
    question_type: str,
    requested_difficulty: int,
) -> list[str]:
    risks: list[str] = []
    existing_questions = existing_question_payloads(conn)
    chunk_bodies = [
        str(chunk.get("body") or "")
        for chunk in prompt_package["user_payload"]["retrieved_chunks"]
    ]
    risks.extend(detect_batch_similarity_risks(questions))
    risks.extend(detect_culture_difficulty_risks(questions, question_type, requested_difficulty))

    for index, question in enumerate(questions, start=1):
        stem = str(question.get("stem") or "")
        normalized_stem = normalize_text(stem)
        if len(normalized_stem) >= 20:
            for chunk_body in chunk_bodies:
                if normalized_stem in normalize_text(chunk_body):
                    risks.append(f"Question {index} stem appears inside a retrieved knowledge chunk.")
                    break

        for row in existing_questions:
            stem_ratio = similarity_ratio(stem, str(row["stem"] or ""))
            payload_text = question_payload_text(question)
            existing_text = str(row["text"] or "")
            payload_ratio = similarity_ratio(payload_text, existing_text)
            active_threshold = (
                AI_DRAFT_SIMILARITY_THRESHOLD
                if row["generation_status"] in {"ai_draft", "ai_review_pending"}
                else threshold
            )
            same_culture_signature = (
                question_type == "culture_choice"
                and row["question_type"] == "culture_choice"
                and is_same_culture_signature(payload_text, existing_text)
            )
            if stem_ratio >= threshold or payload_ratio >= active_threshold or same_culture_signature:
                risks.append(
                    f"Question {index} is too similar to existing question {row['id']} "
                    f"(stem_ratio={stem_ratio:.2f}, payload_ratio={payload_ratio:.2f}, "
                    f"same_culture_signature={same_culture_signature})."
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
    requested_difficulty = int(prompt_package["user_payload"]["generation_request"]["difficulty"])
    similarity_risks = detect_similarity_risks(
        conn,
        questions,
        prompt_package,
        SIMILARITY_THRESHOLD,
        question_type,
        requested_difficulty,
    )
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

    output_path = args.output_dir / f"generation_result_{stamp}.json"
    inserted_ids: list[int] = []
    insert_error: str | None = None
    if args.persist:
        try:
            with connect() as conn:
                inserted_ids = insert_generated_questions(
                    conn,
                    questions,
                    prompt_package,
                    args.question_type,
                    args.knowledge_point,
                )
        except Exception as exc:
            insert_error = str(exc)

    write_json(
        output_path,
        {
            "prompt_path": str(prompt_path),
            "model": args.model,
            "inserted_question_ids": inserted_ids,
            "insert_error": insert_error,
            "assistant_payload": generated_payload,
            "raw_response": response,
        },
    )
    if insert_error:
        raise ValueError(insert_error)
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
