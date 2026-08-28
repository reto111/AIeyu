from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
DEFAULT_REVIEW_CSV = ROOT / "data" / "processed" / "words" / "tem8_words_review_simple.csv"


def fetch_ids(conn: sqlite3.Connection, exam_system_code: str, level_code: str) -> tuple[int, int]:
    system_row = conn.execute(
        "SELECT id FROM exam_systems WHERE code = ?",
        (exam_system_code,),
    ).fetchone()
    if system_row is None:
        raise ValueError(f"Exam system not found: {exam_system_code}")
    exam_system_id = int(system_row[0])
    level_id = int(
        conn.execute(
            "SELECT id FROM exam_levels WHERE exam_system_id = ? AND code = ?",
            (exam_system_id, level_code),
        ).fetchone()[0]
    )
    return exam_system_id, level_id


def fetch_source_id(conn: sqlite3.Connection, exam_system_id: int, source_file: str) -> int:
    row = conn.execute(
        """
        SELECT id
        FROM word_sources
        WHERE exam_system_id = ? AND file_name = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (exam_system_id, source_file),
    ).fetchone()
    if row is None:
        raise ValueError(f"No word_sources row found for {source_file}. Run scripts/migrate_vocabulary.py first.")
    return int(row[0])


def normalized_review_status(value: str) -> str:
    status = (value or "").strip().lower()
    return status or "pending"


def approved_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return [row for row in rows if normalized_review_status(row.get("review_status", "")) == "approved"]


def import_words(
    path: Path,
    dry_run: bool,
    exam_system_code: str,
    level_code: str,
    default_source_file: str,
) -> dict[str, int]:
    rows = approved_rows(path)
    inserted = 0
    updated = 0
    skipped = 0
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        exam_system_id, level_id = fetch_ids(conn, exam_system_code, level_code)
        source_cache: dict[str, int] = {}
        for row in rows:
            word = (row.get("word") or "").strip()
            meaning_zh = (row.get("meaning_zh") or "").strip()
            if not word or not meaning_zh:
                skipped += 1
                continue
            source_file = (row.get("source_file") or default_source_file).strip()
            if source_file not in source_cache:
                source_cache[source_file] = fetch_source_id(conn, exam_system_id, source_file)
            source_id = source_cache[source_file]
            existing = conn.execute(
                """
                SELECT id
                FROM vocabulary_items
                WHERE exam_system_id = ?
                  AND level_id = ?
                  AND word = ?
                  AND COALESCE(part_of_speech, '') = COALESCE(?, '')
                """,
                (exam_system_id, level_id, word, (row.get("part_of_speech") or "").strip() or None),
            ).fetchone()
            if dry_run:
                if existing:
                    updated += 1
                else:
                    inserted += 1
                continue
            if existing:
                conn.execute(
                    """
                    UPDATE vocabulary_items
                    SET lemma = ?,
                        part_of_speech = ?,
                        meaning_zh = ?,
                        source_id = ?,
                        source_page = ?,
                        source_line = ?,
                        raw_text = ?,
                        review_status = 'approved',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        (row.get("lemma") or "").strip() or None,
                        (row.get("part_of_speech") or "").strip() or None,
                        meaning_zh,
                        source_id,
                        int(row["source_page"]) if (row.get("source_page") or "").isdigit() else None,
                        row.get("block_index") or None,
                        row.get("raw_block") or "",
                        int(existing[0]),
                    ),
                )
                updated += 1
            else:
                conn.execute(
                    """
                    INSERT INTO vocabulary_items (
                      exam_system_id, level_id, word, lemma, part_of_speech, meaning_zh,
                      source_id, source_page, source_line, raw_text, review_status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved')
                    """,
                    (
                        exam_system_id,
                        level_id,
                        word,
                        (row.get("lemma") or "").strip() or None,
                        (row.get("part_of_speech") or "").strip() or None,
                        meaning_zh,
                        source_id,
                        int(row["source_page"]) if (row.get("source_page") or "").isdigit() else None,
                        row.get("block_index") or None,
                        row.get("raw_block") or "",
                    ),
                )
                inserted += 1
        if not dry_run:
            conn.commit()
    return {"approved_rows": len(rows), "inserted": inserted, "updated": updated, "skipped": skipped}


def main() -> None:
    parser = argparse.ArgumentParser(description="Import manually approved vocabulary rows.")
    parser.add_argument("--review-csv", type=Path, default=DEFAULT_REVIEW_CSV)
    parser.add_argument("--exam-system", default="TEM8_RU")
    parser.add_argument("--level", default="TEM8")
    parser.add_argument("--default-source-file", default="tem8_russian_words.pdf")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    stats = import_words(
        args.review_csv,
        args.dry_run,
        args.exam_system,
        args.level,
        args.default_source_file,
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
