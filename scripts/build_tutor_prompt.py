from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "prompts" / "tutoring" / "tem8_wrong_question_tutor.md"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "processed" / "tutor_prompts"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compact_wrong_questions(report: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in report.get("wrong_questions", []):
        result.append(
            {
                "quiz_number": item.get("quiz_number"),
                "question_id": item.get("question_id"),
                "question_type": item.get("question_type"),
                "selected_answer": item.get("selected_answer"),
                "correct_answer": item.get("correct_answer"),
                "knowledge_point_codes": item.get("knowledge_point_codes", []),
                "source_label": item.get("source_label"),
                "stem": item.get("stem"),
            }
        )
    return result


def compact_remediation(remediation_pack: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in remediation_pack.get("remediation", []):
        result.append(
            {
                "knowledge_point_code": item.get("knowledge_point_code"),
                "knowledge_point_name_zh": item.get("knowledge_point_name_zh"),
                "attempted_count": item.get("attempted_count"),
                "wrong_count": item.get("wrong_count"),
                "accuracy": item.get("accuracy"),
                "advice_zh": item.get("advice_zh"),
                "practice_questions": [
                    {
                        "question_id": question.get("question_id"),
                        "question_type": question.get("question_type"),
                        "source": question.get("source"),
                        "stem": question.get("stem"),
                        "answer_key": question.get("answer_key"),
                    }
                    for question in item.get("practice_questions", [])
                ],
            }
        )
    return result


def build_payload(report_path: Path, remediation_path: Path) -> dict[str, Any]:
    report = load_json(report_path)
    remediation_pack = load_json(remediation_path)
    return {
        "grading_report": {
            "quiz_session_id": report.get("quiz_session_id"),
            "total_questions": report.get("total_questions"),
            "answered_count": report.get("answered_count"),
            "correct_count": report.get("correct_count"),
            "wrong_count": report.get("wrong_count"),
            "accuracy": report.get("accuracy"),
            "weakness": report.get("weakness", []),
            "wrong_questions": compact_wrong_questions(report),
        },
        "remediation_pack": {
            "summary_zh": remediation_pack.get("summary_zh"),
            "remediation": compact_remediation(remediation_pack),
        },
    }


def build_outputs(report_path: Path, remediation_path: Path, output_path: Path) -> dict[str, str]:
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    payload = build_payload(report_path, remediation_path)
    output = {
        "system_prompt": system_prompt,
        "user_payload": payload,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    markdown_path = output_path.with_suffix(".md")
    markdown_path.write_text(
        "# Tutor Prompt Preview\n\n"
        "## System Prompt\n\n"
        f"{system_prompt}\n\n"
        "## User Payload\n\n"
        "```json\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n"
        "```\n",
        encoding="utf-8",
    )
    return {"json_output": str(output_path), "markdown_output": str(markdown_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an LLM prompt payload for TEM8 wrong-question tutoring.")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--remediation", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    output = args.output or DEFAULT_OUTPUT_DIR / f"{args.report.stem}_tutor_prompt.json"
    result = build_outputs(args.report, args.remediation, output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
