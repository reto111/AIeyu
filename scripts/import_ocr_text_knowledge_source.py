from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

from knowledge_base import (
    ROOT,
    connect,
    ensure_knowledge_base_tables,
    fetch_tem8_ids,
    file_sha256,
    relative_to_root,
)


PAGE_RE = re.compile(r"--- Page\s+(\d+)(?:\s+\([^)]+\))?\s+---")


def parse_pages(text: str) -> list[tuple[int, str]]:
    matches = list(PAGE_RE.finditer(text))
    if not matches:
        return [(1, text.strip())] if text.strip() else []

    pages: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        page_number = int(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            pages.append((page_number, body))
    return pages


def approx_token_count(text: str) -> int:
    return max(len(text) // 2, 1)


def upsert_source(
    conn: sqlite3.Connection,
    exam_system_id: int,
    level_id: int,
    source_pdf: Path,
    title: str,
    source_type: str,
    trust_level: int,
    review_status: str,
    notes: str | None,
) -> int:
    rel_path = relative_to_root(source_pdf)
    existing = conn.execute(
        "SELECT id FROM knowledge_sources WHERE exam_system_id = ? AND file_path = ?",
        (exam_system_id, rel_path),
    ).fetchone()
    file_hash = file_sha256(source_pdf)
    if existing:
        source_id = int(existing["id"])
        conn.execute(
            """
            UPDATE knowledge_sources
            SET level_id = ?, title = ?, source_type = ?, file_hash = ?, language = 'zh',
                trust_level = ?, review_status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (level_id, title, source_type, file_hash, trust_level, review_status, notes, source_id),
        )
        return source_id

    cursor = conn.execute(
        """
        INSERT INTO knowledge_sources (
          exam_system_id, level_id, title, source_type, file_path, file_hash,
          language, trust_level, review_status, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, 'zh', ?, ?, ?)
        """,
        (exam_system_id, level_id, title, source_type, rel_path, file_hash, trust_level, review_status, notes),
    )
    return int(cursor.lastrowid)


def import_ocr_text(
    ocr_text: Path,
    source_pdf: Path,
    title: str,
    source_type: str,
    question_type: str,
    knowledge_point: str,
    trust_level: int,
    review_status: str,
    notes: str | None,
    min_chars: int,
) -> dict[str, Any]:
    text = ocr_text.read_text(encoding="utf-8")
    pages = [(page, body) for page, body in parse_pages(text) if len(body) >= min_chars]

    with connect() as conn:
        ensure_knowledge_base_tables(conn)
        exam_system_id, level_id = fetch_tem8_ids(conn)
        source_id = upsert_source(
            conn,
            exam_system_id,
            level_id,
            source_pdf,
            title,
            source_type,
            trust_level,
            review_status,
            notes,
        )
        conn.execute("DELETE FROM knowledge_chunks WHERE source_id = ?", (source_id,))
        for page_number, body in pages:
            conn.execute(
                """
                INSERT INTO knowledge_chunks (
                  source_id, exam_system_id, level_id, chunk_code, title, body, language,
                  question_type_code, knowledge_point_code, tags_json, source_locator,
                  token_count, review_status
                )
                VALUES (?, ?, ?, ?, ?, ?, 'zh', ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    exam_system_id,
                    level_id,
                    f"{knowledge_point}.p{page_number}",
                    f"{title} p.{page_number}",
                    body,
                    question_type,
                    knowledge_point,
                    json.dumps(["ocr_pdf", "reference_book", "question_generation"], ensure_ascii=False),
                    f"{relative_to_root(source_pdf)}#page-{page_number}",
                    approx_token_count(body),
                    review_status,
                ),
            )
        conn.commit()

    return {
        "source_pdf": relative_to_root(source_pdf),
        "ocr_text": relative_to_root(ocr_text),
        "title": title,
        "pages_imported": len(pages),
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Import OCR text from a scanned reference PDF into knowledge_chunks.")
    parser.add_argument("ocr_text", type=Path)
    parser.add_argument("--source-pdf", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--source-type", default="reference_book")
    parser.add_argument("--question-type", required=True)
    parser.add_argument("--knowledge-point", required=True)
    parser.add_argument("--trust-level", type=int, default=3)
    parser.add_argument("--review-status", choices=["draft", "reviewed", "archived"], default="reviewed")
    parser.add_argument("--notes")
    parser.add_argument("--min-chars", type=int, default=80)
    args = parser.parse_args()

    print(
        json.dumps(
            import_ocr_text(
                ocr_text=args.ocr_text,
                source_pdf=args.source_pdf,
                title=args.title,
                source_type=args.source_type,
                question_type=args.question_type,
                knowledge_point=args.knowledge_point,
                trust_level=args.trust_level,
                review_status=args.review_status,
                notes=args.notes,
                min_chars=args.min_chars,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
