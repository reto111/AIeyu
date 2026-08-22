from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
AUDIT_PATH = ROOT / "data" / "processed" / "question_quality" / "question_quality_manual_review.csv"
OUT_PATH = ROOT / "data" / "processed" / "question_quality" / "question_quality_manual_review_context.csv"


def load_manual_question_ids(path: Path) -> dict[int, list[str]]:
    issues: dict[int, list[str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            question_id = int(row["question_id"])
            issues.setdefault(question_id, []).append(row["issue_code"])
    return issues


def add_source_reference_only_questions(con: sqlite3.Connection, issues: dict[int, list[str]]) -> None:
    rows = con.execute(
        """
        select id
        from questions
        where source_usage = 'source_reference_only'
           or (review_status = 'needs_review' and source_year is not null)
        """
    ).fetchall()
    for row in rows:
        issues.setdefault(row["id"], ["manual_review_required"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Export full context for question quality manual review.")
    parser.add_argument("--db", default=str(DB_PATH), help="SQLite database path.")
    parser.add_argument("--audit", default=str(AUDIT_PATH), help="Manual review CSV from audit script.")
    parser.add_argument("--out", default=str(OUT_PATH), help="Output CSV path.")
    args = parser.parse_args()

    issues_by_id = load_manual_question_ids(Path(args.audit))
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    add_source_reference_only_questions(con, issues_by_id)

    rows: list[dict] = []
    for question_id, issue_codes in sorted(issues_by_id.items()):
        q = con.execute(
            """
            select
              q.id,
              qt.code as type_code,
              q.source_year,
              q.source_question_number,
              q.review_status,
              q.source_usage,
              q.stem,
              q.correct_answer,
              length(coalesce(p.body, '')) as passage_length
            from questions q
            join question_types qt on qt.id = q.question_type_id
            left join passages p on p.id = q.passage_id
            where q.id = ?
            """,
            (question_id,),
        ).fetchone()
        options = {
            row["option_key"]: row["option_text"]
            for row in con.execute(
                """
                select option_key, option_text
                from question_options
                where question_id = ?
                order by sort_order, option_key
                """,
                (question_id,),
            )
        }
        rows.append(
            {
                "question_id": q["id"],
                "source_year": q["source_year"] or "",
                "source_question_number": q["source_question_number"] or "",
                "type_code": q["type_code"],
                "review_status": q["review_status"],
                "source_usage": q["source_usage"],
                "issue_codes": ",".join(sorted(set(issue_codes))),
                "stem": q["stem"],
                "A": options.get("A", ""),
                "B": options.get("B", ""),
                "C": options.get("C", ""),
                "D": options.get("D", ""),
                "correct_answer": q["correct_answer"] or "",
                "passage_length": q["passage_length"],
                "manual_decision": "",
                "manual_note": "",
            }
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "question_id",
        "source_year",
        "source_question_number",
        "type_code",
        "review_status",
        "source_usage",
        "issue_codes",
        "stem",
        "A",
        "B",
        "C",
        "D",
        "correct_answer",
        "passage_length",
        "manual_decision",
        "manual_note",
    ]
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"rows={len(rows)}")
    print(f"out={out_path}")


if __name__ == "__main__":
    main()
