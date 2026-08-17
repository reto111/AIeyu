from __future__ import annotations

import argparse
import json
import random
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "processed" / "remediation"

KNOWLEDGE_POINT_NAMES = {
    "grammar": "语法与词汇",
    "literature": "俄罗斯文学",
    "culture": "俄罗斯国情",
    "reading": "阅读理解",
}


def load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def practice_candidates(
    conn: sqlite3.Connection,
    knowledge_code: str,
    exclude_question_ids: set[int],
) -> list[sqlite3.Row]:
    params: list[Any] = [knowledge_code]
    exclude_clause = ""
    if exclude_question_ids:
        placeholders = ", ".join("?" for _ in exclude_question_ids)
        exclude_clause = f"AND q.id NOT IN ({placeholders})"
        params.extend(sorted(exclude_question_ids))

    return conn.execute(
        f"""
        SELECT
          q.id,
          q.source_year,
          q.source_question_number,
          q.source_label,
          q.stem,
          q.correct_answer,
          qt.code AS question_type,
          p.id AS passage_id,
          p.title AS passage_title,
          p.body AS passage_body
        FROM questions q
        JOIN question_types qt ON qt.id = q.question_type_id
        JOIN question_knowledge_points qkp ON qkp.question_id = q.id
        JOIN knowledge_points kp ON kp.id = qkp.knowledge_point_id
        LEFT JOIN passages p ON p.id = q.passage_id
        WHERE q.review_status = 'approved'
          AND q.source_usage = 'practice'
          AND kp.code = ?
          {exclude_clause}
        ORDER BY q.source_year, CAST(q.source_question_number AS INTEGER), q.id
        """,
        params,
    ).fetchall()


def advice_for_weakness(code: str, attempted: int, wrong: int, accuracy: float) -> str:
    name = KNOWLEDGE_POINT_NAMES.get(code, code)
    if wrong == 0:
        return f"{name}本次表现稳定，可以保持日常复盘节奏。"
    if accuracy < 0.5:
        return f"{name}是本次最需要优先处理的部分。建议先回看错题，整理错误原因，再连续做同类题巩固。"
    return f"{name}已经有一定基础，但仍有失误。建议重点复盘错题对应的定位、概念或搭配，再做少量巩固练习。"


def build_pack(
    report_path: Path,
    output_path: Path,
    per_weakness: int,
    seed: int | None,
) -> dict[str, Any]:
    report = load_report(report_path)
    rng = random.Random(seed)
    wrong_question_ids = {
        int(item["question_id"])
        for item in report.get("wrong_questions", [])
        if item.get("question_id") is not None
    }

    weak_items = [
        item
        for item in report.get("weakness", [])
        if int(item.get("wrong_count", 0)) > 0
    ]
    weak_items.sort(key=lambda item: (-int(item["wrong_count"]), float(item["accuracy"])))

    remediation_items: list[dict[str, Any]] = []
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        for item in weak_items:
            code = item["knowledge_point_code"]
            candidates = practice_candidates(conn, code, wrong_question_ids)
            selected = list(candidates)
            rng.shuffle(selected)
            selected = selected[:per_weakness]

            practice_questions = []
            for row in selected:
                practice_questions.append(
                    {
                        "question_id": row["id"],
                        "question_type": row["question_type"],
                        "stem": row["stem"],
                        "options": option_rows(conn, int(row["id"])),
                        "answer_key": row["correct_answer"],
                        "source": {
                            "year": row["source_year"],
                            "question_number": row["source_question_number"],
                            "label": row["source_label"],
                        },
                        "passage": {
                            "id": row["passage_id"],
                            "title": row["passage_title"],
                            "body": row["passage_body"],
                        }
                        if row["passage_id"]
                        else None,
                    }
                )

            remediation_items.append(
                {
                    "knowledge_point_code": code,
                    "knowledge_point_name_zh": KNOWLEDGE_POINT_NAMES.get(code, code),
                    "attempted_count": item["attempted_count"],
                    "wrong_count": item["wrong_count"],
                    "accuracy": item["accuracy"],
                    "wrong_question_numbers": item.get("wrong_question_numbers", []),
                    "advice_zh": advice_for_weakness(
                        code,
                        int(item["attempted_count"]),
                        int(item["wrong_count"]),
                        float(item["accuracy"]),
                    ),
                    "practice_questions": practice_questions,
                }
            )

    pack = {
        "source_report": str(report_path),
        "total_questions": report["total_questions"],
        "correct_count": report["correct_count"],
        "accuracy": report["accuracy"],
        "summary_zh": summary_zh(report, remediation_items),
        "remediation": remediation_items,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    return pack


def summary_zh(report: dict[str, Any], remediation_items: list[dict[str, Any]]) -> str:
    total = report["total_questions"]
    correct = report["correct_count"]
    accuracy = float(report["accuracy"])
    if not remediation_items:
        return f"本次 {total} 题答对 {correct} 题，正确率 {accuracy:.0%}。本次没有明显薄弱知识点。"
    names = "、".join(item["knowledge_point_name_zh"] for item in remediation_items)
    return f"本次 {total} 题答对 {correct} 题，正确率 {accuracy:.0%}。需要优先复盘：{names}。"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a remediation pack from a graded TEM8 quiz report.")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--per-weakness", type=int, default=3)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()

    output = args.output or DEFAULT_OUTPUT_DIR / f"{args.report.stem}_remediation.json"
    pack = build_pack(args.report, output, args.per_weakness, args.seed)
    print(
        json.dumps(
            {
                "output": str(output),
                "weakness_count": len(pack["remediation"]),
                "summary_zh": pack["summary_zh"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
