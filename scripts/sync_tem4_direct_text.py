from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
DEFAULT_INPUT = ROOT / "data" / "processed" / "structured" / "tem4_direct_rebuilt"

def source_document_id(conn: sqlite3.Connection, year: int) -> int:
    row = conn.execute(
        """SELECT sd.id
           FROM source_documents sd
           JOIN exam_systems es ON es.id = sd.exam_system_id
           WHERE es.code = 'TEM4_RU' AND sd.source_year = ?
             AND sd.document_type IN ('full', 'questions')
           ORDER BY CASE sd.document_type WHEN 'full' THEN 0 ELSE 1 END, sd.id
           LIMIT 1""",
        (year,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Missing TEM4 source document for {year}.")
    return int(row[0])


def get_passage(
    conn: sqlite3.Connection,
    source_id: int,
    payload: dict[str, Any] | None,
    cache: dict[tuple[int, str], int],
) -> int | None:
    if not payload or not payload.get("body"):
        return None
    title = str(payload.get("title") or "")
    body = str(payload.get("body") or "").replace("沙拉俄语", "").strip()
    key = (source_id, title)
    if key in cache:
        return cache[key]
    row = conn.execute(
        "SELECT id FROM passages WHERE source_document_id=? AND COALESCE(title,'')=? ORDER BY id LIMIT 1",
        (source_id, title),
    ).fetchone()
    if row:
        passage_id = int(row[0])
        conn.execute(
            "UPDATE passages SET title=?, body=?, language='ru' WHERE id=?",
            (title, body, passage_id),
        )
    else:
        passage_id = int(
            conn.execute(
                "INSERT INTO passages (source_document_id,title,body,language) VALUES (?,?,?,'ru')",
                (source_id, title, body),
            ).lastrowid
        )
    cache[key] = passage_id
    return passage_id


def sync_file(conn: sqlite3.Connection, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    year = int(payload["source_year"])
    source_id = source_document_id(conn, year)
    exam_id = int(conn.execute("SELECT id FROM exam_systems WHERE code='TEM4_RU'").fetchone()[0])
    cache: dict[tuple[int, str], int] = {}
    synced = 0
    missing_existing: list[str] = []
    for item in payload.get("questions", []):
        number = str(item["source_question_number"])
        row = conn.execute(
            "SELECT id FROM questions WHERE exam_system_id=? AND source_year=? AND source_question_number=?",
            (exam_id, year, number),
        ).fetchone()
        if row is None:
            missing_existing.append(number)
            continue
        question_id = int(row[0])
        type_id = int(conn.execute("SELECT id FROM question_types WHERE code=?", (item["question_type"],)).fetchone()[0])
        passage_id = get_passage(conn, source_id, item.get("passage"), cache)
        stem = str(item.get("stem") or "").replace("沙拉俄语", "").strip()
        raw_text = str(item.get("raw_text") or "").replace("沙拉俄语", "").strip()
        conn.execute(
            """UPDATE questions
               SET level_id=(SELECT id FROM exam_levels WHERE exam_system_id=? AND code='TEM4'),
                   question_type_id=?, passage_id=?, source_document_id=?,
                   stem=?, correct_answer=?, source_page=?, raw_text=?,
                   review_status='needs_review', source_usage='source_reference_only',
                   content_origin='past_exam_original', source_label=?,
                   requires_source_label=1, updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (
                exam_id,
                type_id,
                passage_id,
                source_id,
                stem,
                item.get("correct_answer") or None,
                item.get("source_page"),
                raw_text,
                f"{year} 年俄语专四真题",
                question_id,
            ),
        )
        conn.execute("DELETE FROM question_options WHERE question_id=?", (question_id,))
        for order, option in enumerate(item.get("options") or []):
            text = str(option.get("text") or "").replace("沙拉俄语", "").strip()
            conn.execute(
                "INSERT INTO question_options (question_id,option_key,option_text,sort_order) VALUES (?,?,?,?)",
                (question_id, option.get("key"), text, order),
            )
        conn.execute(
            """INSERT INTO question_review_logs
               (question_id, review_decision, review_notes, reviewer)
               VALUES (?, 'needs_review', ?, 'direct_text_resync')""",
            (question_id, "replaced OCR-derived fields with direct PDF text layer; batch review required"),
        )
        synced += 1
    return {"year": year, "synced": synced, "missing_existing": missing_existing}


def main() -> None:
    parser = argparse.ArgumentParser(description="Resync TEM4 2017-2023 from direct PDF text extraction.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    backup = args.db.parent.parent / "data" / "processed" / "backups" / (
        "russian_ai_tutor_before_tem4_direct_text_resync_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".sqlite"
    )
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.db, backup)

    results = []
    with sqlite3.connect(args.db) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        for year in (2017, 2018, 2019, 2021, 2022, 2023):
            path = args.input_dir / f"tem4_russian_{year}_review.json"
            results.append(sync_file(conn, path))
        conn.commit()
    print(json.dumps({"backup": str(backup), "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

