from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
DEFAULT_INPUT = ROOT / "data" / "processed" / "review_sheets" / "tem8_questions_review.csv"
VALID_DECISIONS = {"approved", "needs_review", "needs_fix", "rejected"}
STATUS_BY_DECISION = {
    "approved": "approved",
    "needs_review": "needs_review",
    "needs_fix": "needs_review",
    "rejected": "rejected",
}


def normalize(value: str | None) -> str:
    return (value or "").strip().lstrip("\ufeff")


def parse_codes(value: str | None) -> list[str]:
    raw = normalize(value)
    if not raw:
        return []
    codes = [item.strip() for item in raw.replace(";", ",").split(",") if item.strip()]
    return list(dict.fromkeys(codes))


def knowledge_point_ids(conn: sqlite3.Connection, codes: list[str]) -> dict[str, int]:
    if not codes:
        return {}
    placeholders = ", ".join("?" for _ in codes)
    rows = conn.execute(
        f"SELECT code, id FROM knowledge_points WHERE code IN ({placeholders})",
        codes,
    ).fetchall()
    found = {str(code): int(point_id) for code, point_id in rows}
    missing = sorted(set(codes) - set(found))
    if missing:
        raise ValueError(f"Unknown knowledge point code(s): {', '.join(missing)}")
    return found


def ensure_question_exists(conn: sqlite3.Connection, question_id: int) -> None:
    row = conn.execute("SELECT id FROM questions WHERE id = ?", (question_id,)).fetchone()
    if row is None:
        raise ValueError(f"Question id not found: {question_id}")


def apply_row(
    conn: sqlite3.Connection,
    row: dict[str, str],
    reviewer: str,
    require_knowledge_for_approved: bool,
) -> str:
    question_id_raw = normalize(row.get("question_id"))
    if not question_id_raw:
        return "skipped_blank_question_id"
    question_id = int(question_id_raw)
    ensure_question_exists(conn, question_id)

    decision = normalize(row.get("review_decision"))
    if not decision:
        return "skipped_blank_decision"
    if decision not in VALID_DECISIONS:
        raise ValueError(f"Invalid review_decision for question {question_id}: {decision}")

    codes = parse_codes(row.get("knowledge_point_codes"))
    if decision == "approved" and require_knowledge_for_approved and not codes:
        raise ValueError(f"Approved question {question_id} must have at least one knowledge point code.")

    code_to_id = knowledge_point_ids(conn, codes)
    if codes:
        conn.execute("DELETE FROM question_knowledge_points WHERE question_id = ?", (question_id,))
        for code in codes:
            conn.execute(
                """
                INSERT INTO question_knowledge_points (question_id, knowledge_point_id, weight)
                VALUES (?, ?, 1.0)
                """,
                (question_id, code_to_id[code]),
            )

    conn.execute(
        """
        UPDATE questions
        SET review_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (STATUS_BY_DECISION[decision], question_id),
    )
    conn.execute(
        """
        INSERT INTO question_review_logs (
          question_id, review_decision, review_notes, knowledge_point_codes, reviewer
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            question_id,
            decision,
            normalize(row.get("review_notes")) or None,
            ",".join(codes) if codes else None,
            reviewer,
        ),
    )
    return f"applied_{decision}"


def apply_review_sheet(
    input_path: Path,
    reviewer: str,
    dry_run: bool,
    require_knowledge_for_approved: bool,
) -> dict[str, Any]:
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    summary: dict[str, int] = {}
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for row in rows:
            result = apply_row(conn, row, reviewer, require_knowledge_for_approved)
            summary[result] = summary.get(result, 0) + 1
        if dry_run:
            conn.rollback()
        else:
            conn.commit()

    return {"input": str(input_path), "dry_run": dry_run, "summary": summary}


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply manual review decisions from a TEM8 review CSV.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--reviewer", default="manual_review")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--allow-approved-without-knowledge",
        action="store_true",
        help="Allow approved rows without knowledge_point_codes.",
    )
    args = parser.parse_args()
    result = apply_review_sheet(
        input_path=args.input,
        reviewer=args.reviewer,
        dry_run=args.dry_run,
        require_knowledge_for_approved=not args.allow_approved_without_knowledge,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


