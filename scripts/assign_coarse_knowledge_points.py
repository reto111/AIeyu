from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"

QUESTION_TYPE_TO_KNOWLEDGE = {
    "grammar_choice": "grammar",
    "literature_choice": "literature",
    "culture_choice": "culture",
    "reading_choice": "reading",
}


def knowledge_ids(conn: sqlite3.Connection) -> dict[str, int]:
    codes = list(QUESTION_TYPE_TO_KNOWLEDGE.values())
    placeholders = ", ".join("?" for _ in codes)
    rows = conn.execute(
        f"SELECT code, id FROM knowledge_points WHERE code IN ({placeholders})",
        codes,
    ).fetchall()
    found = {str(code): int(point_id) for code, point_id in rows}
    missing = sorted(set(codes) - set(found))
    if missing:
        raise ValueError(f"Missing coarse knowledge point(s): {', '.join(missing)}")
    return found


def candidate_rows(
    conn: sqlite3.Connection,
    years: list[int],
    review_status: str | None,
    only_missing: bool,
) -> list[sqlite3.Row]:
    filters = ["qt.code IN ('grammar_choice', 'literature_choice', 'culture_choice', 'reading_choice')"]
    params: list[Any] = []

    if years:
        placeholders = ", ".join("?" for _ in years)
        filters.append(f"q.source_year IN ({placeholders})")
        params.extend(years)

    if review_status:
        filters.append("q.review_status = ?")
        params.append(review_status)

    if only_missing:
        filters.append(
            """
            NOT EXISTS (
              SELECT 1
              FROM question_knowledge_points qkp
              WHERE qkp.question_id = q.id
            )
            """
        )

    return conn.execute(
        f"""
        SELECT q.id, q.source_year, q.source_question_number, qt.code AS question_type
        FROM questions q
        JOIN question_types qt ON qt.id = q.question_type_id
        WHERE {" AND ".join(filters)}
        ORDER BY q.source_year, CAST(q.source_question_number AS INTEGER), q.id
        """,
        params,
    ).fetchall()


def assign_coarse_knowledge(
    years: list[int],
    review_status: str | None,
    replace_existing: bool,
    dry_run: bool,
) -> dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        code_to_id = knowledge_ids(conn)
        rows = candidate_rows(
            conn,
            years=years,
            review_status=review_status,
            only_missing=not replace_existing,
        )

        summary: dict[str, int] = {}
        for row in rows:
            question_type = str(row["question_type"])
            knowledge_code = QUESTION_TYPE_TO_KNOWLEDGE[question_type]
            summary[knowledge_code] = summary.get(knowledge_code, 0) + 1

            if replace_existing:
                conn.execute(
                    "DELETE FROM question_knowledge_points WHERE question_id = ?",
                    (int(row["id"]),),
                )
            conn.execute(
                """
                INSERT INTO question_knowledge_points (question_id, knowledge_point_id, weight)
                VALUES (?, ?, 1.0)
                """,
                (int(row["id"]), code_to_id[knowledge_code]),
            )

        if dry_run:
            conn.rollback()
        else:
            conn.commit()

    return {
        "years": years or "all",
        "review_status": review_status or "all",
        "replace_existing": replace_existing,
        "dry_run": dry_run,
        "assigned_total": sum(summary.values()),
        "assigned_by_knowledge": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Assign coarse TEM8 knowledge points by question type.")
    parser.add_argument("--year", type=int, action="append", default=[])
    parser.add_argument("--review-status", default="needs_review")
    parser.add_argument("--replace-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = assign_coarse_knowledge(
        years=args.year,
        review_status=args.review_status,
        replace_existing=args.replace_existing,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
