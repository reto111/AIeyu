from __future__ import annotations

import argparse
import json
import random
import sqlite3
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "processed" / "quizzes"
DEFAULT_RANDOM_QUESTION_TYPES = ["grammar_choice", "literature_choice", "culture_choice"]
READING_QUESTION_TYPE = "reading_choice"


def parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def option_rows(conn: sqlite3.Connection, question_id: int) -> list[dict[str, str]]:
    rows = conn.execute(
        """
        SELECT option_key, option_text
        FROM question_options
        WHERE question_id = ?
        ORDER BY sort_order, option_key
        """,
        (question_id,),
    ).fetchall()
    return [{"key": row[0], "text": row[1]} for row in rows]


def knowledge_codes(conn: sqlite3.Connection, question_id: int) -> list[str]:
    rows = conn.execute(
        """
        SELECT kp.code
        FROM question_knowledge_points qkp
        JOIN knowledge_points kp ON kp.id = qkp.knowledge_point_id
        WHERE qkp.question_id = ?
        ORDER BY kp.sort_order, kp.code
        """,
        (question_id,),
    ).fetchall()
    return [row[0] for row in rows]


def source_question_number(row: sqlite3.Row) -> int:
    try:
        return int(row["source_question_number"])
    except (TypeError, ValueError):
        return 0


def complete_question_units(rows: list[sqlite3.Row]) -> list[list[sqlite3.Row]]:
    units: list[list[sqlite3.Row]] = []
    reading_groups: dict[int, list[sqlite3.Row]] = {}

    for row in rows:
        if row["question_type"] == READING_QUESTION_TYPE and row["passage_id"]:
            reading_groups.setdefault(int(row["passage_id"]), []).append(row)
        else:
            units.append([row])

    for group in reading_groups.values():
        units.append(sorted(group, key=source_question_number))

    return units


def select_complete_units(
    rows: list[sqlite3.Row],
    target_count: int,
    rng: random.Random,
) -> list[sqlite3.Row]:
    selected: list[sqlite3.Row] = []
    units = complete_question_units(rows)
    rng.shuffle(units)
    for unit in units:
        selected.extend(unit)
        if len(selected) >= target_count:
            break
    return selected


def candidate_rows(
    conn: sqlite3.Connection,
    question_types: list[str],
    years: list[int],
    include_needs_review: bool,
) -> list[sqlite3.Row]:
    params: list[Any] = []
    filters = ["q.source_usage = 'practice'"]
    if include_needs_review:
        filters.append("q.review_status IN ('approved', 'needs_review')")
    else:
        filters.append("q.review_status = 'approved'")

    if question_types:
        placeholders = ", ".join("?" for _ in question_types)
        filters.append(f"qt.code IN ({placeholders})")
        params.extend(question_types)

    if years:
        placeholders = ", ".join("?" for _ in years)
        filters.append(f"q.source_year IN ({placeholders})")
        params.extend(years)

    where_clause = " AND ".join(filters)
    return conn.execute(
        f"""
        SELECT
          q.id,
          q.source_year,
          q.source_question_number,
          q.source_label,
          q.requires_source_label,
          q.content_origin,
          q.review_status,
          q.stem,
          q.correct_answer,
          qt.code AS question_type,
          p.id AS passage_id,
          p.title AS passage_title,
          p.body AS passage_body
        FROM questions q
        JOIN question_types qt ON qt.id = q.question_type_id
        LEFT JOIN passages p ON p.id = q.passage_id
        WHERE {where_clause}
        ORDER BY q.source_year, CAST(q.source_question_number AS INTEGER), q.id
        """,
        params,
    ).fetchall()


def generate_quiz(
    count: int,
    question_types: list[str],
    years: list[int],
    include_needs_review: bool,
    seed: int | None,
) -> dict[str, Any]:
    rng = random.Random(seed)
    effective_question_types = question_types or DEFAULT_RANDOM_QUESTION_TYPES
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        candidates = candidate_rows(conn, effective_question_types, years, include_needs_review)
        if len(candidates) < count:
            raise ValueError(f"Only {len(candidates)} candidate question(s), cannot generate {count}.")
        selected = select_complete_units(list(candidates), count, rng)

        questions = []
        for index, row in enumerate(selected, start=1):
            source_label = row["source_label"] if row["requires_source_label"] else None
            questions.append(
                {
                    "quiz_number": index,
                    "question_id": row["id"],
                    "question_type": row["question_type"],
                    "stem": row["stem"],
                    "options": option_rows(conn, row["id"]),
                    "answer_key": row["correct_answer"],
                    "source": {
                        "year": row["source_year"],
                        "question_number": row["source_question_number"],
                        "label": source_label,
                        "content_origin": row["content_origin"],
                    },
                    "review_status": row["review_status"],
                    "knowledge_point_codes": knowledge_codes(conn, row["id"]),
                    "passage": {
                        "id": row["passage_id"],
                        "title": row["passage_title"],
                        "body": row["passage_body"],
                    }
                    if row["passage_id"]
                    else None,
                }
            )

    return {
        "exam_system": "TEM8_RU",
        "level": "TEM8",
        "count": len(questions),
        "requested_count": count,
        "question_types": effective_question_types,
        "years": years or "all",
        "include_needs_review": include_needs_review,
        "seed": seed,
        "questions": questions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a TEM8 practice quiz from the structured question bank.")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--type", dest="question_types", action="append", help="Question type code. Can be repeated.")
    parser.add_argument("--year", type=int, action="append", help="Source year. Can be repeated.")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--include-needs-review", action="store_true", help="Internal smoke-test option before manual approval.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        quiz = generate_quiz(
            count=args.count,
            question_types=args.question_types or [],
            years=args.year or [],
            include_needs_review=args.include_needs_review,
            seed=args.seed,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(2) from exc

    output_path = args.output
    if output_path is None:
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        suffix = args.seed if args.seed is not None else "random"
        output_path = DEFAULT_OUTPUT_DIR / f"tem8_quiz_{suffix}.json"
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(json.dumps(quiz, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output_path), "count": quiz["count"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


