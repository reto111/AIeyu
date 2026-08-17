from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED_COUNTS = {
    "grammar_choice": 17,
    "literature_choice": 7,
    "culture_choice": 6,
    "reading_choice": 20,
}


def validate_file(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    questions = payload.get("questions", [])

    counts: dict[str, int] = {}
    missing_options: list[str] = []
    missing_answers: list[str] = []
    missing_passages: list[str] = []
    missing_source_labels: list[str] = []

    for question in questions:
        question_type = question.get("question_type")
        number = question.get("source_question_number")
        counts[question_type] = counts.get(question_type, 0) + 1

        if len(question.get("options", [])) != 4:
            missing_options.append(str(number))
        if not question.get("correct_answer"):
            missing_answers.append(str(number))
        if question_type == "reading_choice" and not question.get("passage", {}).get("body"):
            missing_passages.append(str(number))
        if question.get("content_origin") == "past_exam_original":
            if not question.get("requires_source_label") or not question.get("source_label"):
                missing_source_labels.append(str(number))

    errors: list[str] = []
    if len(questions) != 50:
        errors.append(f"expected 50 questions, got {len(questions)}")

    for question_type, expected_count in EXPECTED_COUNTS.items():
        actual_count = counts.get(question_type, 0)
        if actual_count != expected_count:
            errors.append(f"expected {expected_count} {question_type}, got {actual_count}")

    if missing_options:
        errors.append(f"missing or invalid options: {', '.join(missing_options)}")
    if missing_answers:
        errors.append(f"missing answers: {', '.join(missing_answers)}")
    if missing_passages:
        errors.append(f"reading questions missing passages: {', '.join(missing_passages)}")
    if missing_source_labels:
        errors.append(
            "past exam questions must require and include a source label: "
            + ", ".join(missing_source_labels)
        )

    if payload.get("content_origin") == "past_exam_original":
        if not payload.get("requires_source_label") or not payload.get("source_label"):
            errors.append("payload must require and include a source label")

    return {
        "file": str(path),
        "source_year": payload.get("source_year"),
        "counts": counts,
        "question_total": len(questions),
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate TEM8 review JSON files.")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    results = [validate_file(path) for path in args.paths]
    print(json.dumps(results, ensure_ascii=False, indent=2))

    failed = [result for result in results if result["errors"]]
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
