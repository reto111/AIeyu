from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path("database/russian_ai_tutor.sqlite")


def fetch_one_id(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> int:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise ValueError(f"Missing database row for query: {sql} {params}")
    return int(row[0])


def source_document_id(conn: sqlite3.Connection, source_year: int) -> int:
    row = conn.execute(
        """
        SELECT sd.id
        FROM source_documents sd
        JOIN exam_systems es ON es.id = sd.exam_system_id
        WHERE es.code = 'TEM8_RU'
          AND sd.source_year = ?
          AND sd.document_type = 'full'
        ORDER BY sd.id
        LIMIT 1
        """,
        (source_year,),
    ).fetchone()
    if row is None:
        raise ValueError(f"No TEM8 full source document found for year {source_year}")
    return int(row[0])


def delete_existing_source_items(conn: sqlite3.Connection, source_document_id_value: int) -> None:
    question_ids = [
        row[0]
        for row in conn.execute(
            "SELECT id FROM questions WHERE source_document_id = ?",
            (source_document_id_value,),
        ).fetchall()
    ]
    for question_id in question_ids:
        conn.execute("DELETE FROM question_options WHERE question_id = ?", (question_id,))
        conn.execute("DELETE FROM question_knowledge_points WHERE question_id = ?", (question_id,))
    conn.execute("DELETE FROM questions WHERE source_document_id = ?", (source_document_id_value,))
    conn.execute("DELETE FROM passages WHERE source_document_id = ?", (source_document_id_value,))


def get_or_create_passage(
    conn: sqlite3.Connection,
    source_document_id_value: int,
    passage_payload: dict[str, Any] | None,
    passage_cache: dict[tuple[str, str], int],
) -> int | None:
    if not passage_payload:
        return None

    title = passage_payload.get("title") or ""
    body = passage_payload.get("body") or ""
    cache_key = (title, body)
    if cache_key in passage_cache:
        return passage_cache[cache_key]

    existing = conn.execute(
        """
        SELECT id
        FROM passages
        WHERE source_document_id = ?
          AND COALESCE(title, '') = ?
          AND body = ?
        """,
        (source_document_id_value, title, body),
    ).fetchone()
    if existing:
        passage_id = int(existing[0])
    else:
        cursor = conn.execute(
            """
            INSERT INTO passages (source_document_id, title, body, language)
            VALUES (?, ?, ?, 'ru')
            """,
            (source_document_id_value, title, body),
        )
        passage_id = int(cursor.lastrowid)

    passage_cache[cache_key] = passage_id
    return passage_id


def insert_question(
    conn: sqlite3.Connection,
    question: dict[str, Any],
    exam_system_id: int,
    level_id: int,
    question_type_id: int,
    source_document_id_value: int,
    passage_id: int | None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO questions (
          exam_system_id, level_id, question_type_id, passage_id, source_document_id,
          source_year, source_question_number, stem, correct_answer, explanation_zh,
          difficulty, review_status, generation_status, source_page, raw_text,
          source_usage, content_origin, source_label, requires_source_label,
          similarity_review_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            exam_system_id,
            level_id,
            question_type_id,
            passage_id,
            source_document_id_value,
            question.get("source_year"),
            question.get("source_question_number"),
            question.get("stem") or "",
            question.get("correct_answer"),
            question.get("explanation_zh"),
            question.get("difficulty"),
            question.get("review_status", "needs_review"),
            question.get("generation_status", "human_imported"),
            question.get("source_page"),
            question.get("raw_text"),
            question.get("source_usage", "practice"),
            question.get("content_origin", "past_exam_original"),
            question.get("source_label"),
            1 if question.get("requires_source_label") else 0,
            question.get("similarity_review_status", "not_checked"),
        ),
    )
    return int(cursor.lastrowid)


def insert_options(conn: sqlite3.Connection, question_id: int, options: list[dict[str, Any]]) -> None:
    for index, option in enumerate(options):
        conn.execute(
            """
            INSERT INTO question_options (question_id, option_key, option_text, sort_order)
            VALUES (?, ?, ?, ?)
            """,
            (question_id, option.get("key"), option.get("text") or "", index),
        )


def import_review_json(conn: sqlite3.Connection, path: Path, replace_source: bool) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    source_year = int(payload["source_year"])
    source_document_id_value = source_document_id(conn, source_year)

    if replace_source:
        delete_existing_source_items(conn, source_document_id_value)

    exam_system_id = fetch_one_id(conn, "SELECT id FROM exam_systems WHERE code = ?", ("TEM8_RU",))
    level_id = fetch_one_id(
        conn,
        """
        SELECT id
        FROM exam_levels
        WHERE exam_system_id = ? AND code = 'TEM8'
        """,
        (exam_system_id,),
    )

    passage_cache: dict[tuple[str, str], int] = {}
    inserted = 0
    skipped_existing = 0

    for question in payload.get("questions", []):
        existing = conn.execute(
            """
            SELECT id
            FROM questions
            WHERE source_document_id = ?
              AND source_question_number = ?
              AND content_origin = ?
            """,
            (
                source_document_id_value,
                question.get("source_question_number"),
                question.get("content_origin", "past_exam_original"),
            ),
        ).fetchone()
        if existing:
            skipped_existing += 1
            continue

        question_type_id = fetch_one_id(
            conn,
            "SELECT id FROM question_types WHERE code = ?",
            (question["question_type"],),
        )
        passage_id = get_or_create_passage(
            conn,
            source_document_id_value,
            question.get("passage"),
            passage_cache,
        )
        question_id = insert_question(
            conn,
            question,
            exam_system_id,
            level_id,
            question_type_id,
            source_document_id_value,
            passage_id,
        )
        insert_options(conn, question_id, question.get("options", []))
        inserted += 1

    return {
        "file": str(path),
        "source_year": source_year,
        "inserted": inserted,
        "skipped_existing": skipped_existing,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import TEM8 review JSON into SQLite.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument(
        "--replace-source",
        action="store_true",
        help="Delete existing imported questions/passages for each source year before importing.",
    )
    args = parser.parse_args()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        results = [import_review_json(conn, path, args.replace_source) for path in args.paths]
        conn.commit()

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
