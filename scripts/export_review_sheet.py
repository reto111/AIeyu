from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "review_sheets" / "tem8_questions_review.csv"
DEFAULT_PASSAGES_OUTPUT = ROOT / "data" / "processed" / "review_sheets" / "tem8_passages_review.csv"

FIELDNAMES = [
    "question_id",
    "source_year",
    "source_question_number",
    "source_label",
    "question_type",
    "review_status",
    "content_origin",
    "stem",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_answer",
    "passage_id",
    "passage_title",
    "knowledge_point_codes",
    "review_decision",
    "review_notes",
]

PASSAGE_FIELDNAMES = [
    "passage_id",
    "source_year",
    "source_label",
    "passage_title",
    "passage_body",
    "review_notes",
]


def safe_cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def option_map(conn: sqlite3.Connection, question_id: int) -> dict[str, str]:
    rows = conn.execute(
        """
        SELECT option_key, option_text
        FROM question_options
        WHERE question_id = ?
        ORDER BY sort_order, option_key
        """,
        (question_id,),
    ).fetchall()
    return {str(key).upper(): text for key, text in rows}


def review_rows(conn: sqlite3.Connection, years: list[int] | None) -> list[dict[str, str]]:
    params: list[Any] = []
    year_filter = ""
    if years:
        placeholders = ", ".join("?" for _ in years)
        year_filter = f"AND q.source_year IN ({placeholders})"
        params.extend(years)

    rows = conn.execute(
        f"""
        SELECT
          q.id AS question_id,
          q.source_year,
          q.source_question_number,
          q.source_label,
          qt.code AS question_type,
          q.review_status,
          q.content_origin,
          q.stem,
          q.correct_answer,
          q.passage_id,
          p.title AS passage_title
        FROM questions q
        JOIN question_types qt ON qt.id = q.question_type_id
        LEFT JOIN passages p ON p.id = q.passage_id
        WHERE q.review_status = 'needs_review'
          {year_filter}
        ORDER BY q.source_year, CAST(q.source_question_number AS INTEGER), q.id
        """,
        params,
    ).fetchall()

    result: list[dict[str, str]] = []
    for row in rows:
        question_id = int(row["question_id"])
        options = option_map(conn, question_id)
        result.append(
            {
                "question_id": safe_cell(question_id),
                "source_year": safe_cell(row["source_year"]),
                "source_question_number": safe_cell(row["source_question_number"]),
                "source_label": safe_cell(row["source_label"]),
                "question_type": safe_cell(row["question_type"]),
                "review_status": safe_cell(row["review_status"]),
                "content_origin": safe_cell(row["content_origin"]),
                "stem": safe_cell(row["stem"]),
                "option_a": safe_cell(options.get("A")),
                "option_b": safe_cell(options.get("B")),
                "option_c": safe_cell(options.get("C")),
                "option_d": safe_cell(options.get("D")),
                "correct_answer": safe_cell(row["correct_answer"]),
                "passage_id": safe_cell(row["passage_id"]),
                "passage_title": safe_cell(row["passage_title"]),
                "knowledge_point_codes": "",
                "review_decision": "",
                "review_notes": "",
            }
        )
    return result


def passage_rows(conn: sqlite3.Connection, years: list[int] | None) -> list[dict[str, str]]:
    params: list[Any] = []
    year_filter = ""
    if years:
        placeholders = ", ".join("?" for _ in years)
        year_filter = f"AND q.source_year IN ({placeholders})"
        params.extend(years)

    rows = conn.execute(
        f"""
        SELECT DISTINCT
          p.id AS passage_id,
          q.source_year,
          q.source_label,
          p.title AS passage_title,
          p.body AS passage_body
        FROM questions q
        JOIN passages p ON p.id = q.passage_id
        WHERE q.review_status = 'needs_review'
          {year_filter}
        ORDER BY q.source_year, p.id
        """,
        params,
    ).fetchall()

    return [
        {
            "passage_id": safe_cell(row["passage_id"]),
            "source_year": safe_cell(row["source_year"]),
            "source_label": safe_cell(row["source_label"]),
            "passage_title": safe_cell(row["passage_title"]),
            "passage_body": safe_cell(row["passage_body"]),
            "review_notes": "",
        }
        for row in rows
    ]


def export_review_sheet(
    output_path: Path,
    passages_output_path: Path,
    years: list[int] | None,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    passages_output_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = review_rows(conn, years)
        passages = passage_rows(conn, years)

    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    with passages_output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=PASSAGE_FIELDNAMES)
        writer.writeheader()
        writer.writerows(passages)

    return {
        "questions_output": str(output_path),
        "question_rows": len(rows),
        "passages_output": str(passages_output_path),
        "passage_rows": len(passages),
        "years": years or "all",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export pending TEM8 questions for manual review.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--passages-output", type=Path, default=DEFAULT_PASSAGES_OUTPUT)
    parser.add_argument("--year", type=int, action="append", help="Limit export to one source year. Can be repeated.")
    args = parser.parse_args()
    result = export_review_sheet(args.output, args.passages_output, args.year)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
