from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
DEFAULT_REPORT_DIR = ROOT / "data" / "processed" / "reports"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_answer(value: Any) -> str:
    return str(value or "").strip().upper()


def answers_by_quiz_number(payload: dict[str, Any]) -> dict[int, str]:
    raw_answers = payload.get("answers", payload)
    result: dict[int, str] = {}

    if isinstance(raw_answers, dict):
        for key, value in raw_answers.items():
            result[int(key)] = normalize_answer(value)
        return result

    if isinstance(raw_answers, list):
        for item in raw_answers:
            quiz_number = int(item["quiz_number"])
            result[quiz_number] = normalize_answer(item.get("selected_answer"))
        return result

    raise ValueError("Answers must be a dict or a list under the 'answers' key.")


def fetch_ids(conn: sqlite3.Connection) -> tuple[int, int]:
    exam_row = conn.execute("SELECT id FROM exam_systems WHERE code = 'TEM8_RU'").fetchone()
    if exam_row is None:
        raise ValueError("Missing exam system TEM8_RU.")
    exam_system_id = int(exam_row[0])

    level_row = conn.execute(
        "SELECT id FROM exam_levels WHERE exam_system_id = ? AND code = 'TEM8'",
        (exam_system_id,),
    ).fetchone()
    if level_row is None:
        raise ValueError("Missing TEM8 level.")
    return exam_system_id, int(level_row[0])


def knowledge_point_ids(conn: sqlite3.Connection, codes: list[str]) -> list[int]:
    if not codes:
        return []
    placeholders = ", ".join("?" for _ in codes)
    rows = conn.execute(
        f"SELECT id FROM knowledge_points WHERE code IN ({placeholders})",
        codes,
    ).fetchall()
    return [int(row[0]) for row in rows]


def create_quiz_session(
    conn: sqlite3.Connection,
    quiz: dict[str, Any],
    title: str,
    user_id: int | None,
) -> int:
    exam_system_id, level_id = fetch_ids(conn)
    cursor = conn.execute(
        """
        INSERT INTO quiz_sessions (
          user_id, exam_system_id, level_id, title, mode, status, total_questions
        )
        VALUES (?, ?, ?, ?, 'random', 'submitted', ?)
        """,
        (user_id, exam_system_id, level_id, title, int(quiz["count"])),
    )
    return int(cursor.lastrowid)


def grade_quiz(
    quiz_path: Path,
    answers_path: Path,
    output_path: Path,
    persist: bool,
    user_id: int | None,
    title: str | None,
) -> dict[str, Any]:
    quiz = load_json(quiz_path)
    answers = answers_by_quiz_number(load_json(answers_path))
    questions = quiz.get("questions", [])
    if not questions:
        raise ValueError("Quiz has no questions.")

    graded_questions: list[dict[str, Any]] = []
    weakness: dict[str, dict[str, Any]] = {}
    correct_count = 0

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        quiz_session_id = None
        if persist:
            quiz_session_id = create_quiz_session(
                conn,
                quiz,
                title or quiz_path.stem,
                user_id,
            )

        for question in questions:
            quiz_number = int(question["quiz_number"])
            selected = answers.get(quiz_number, "")
            correct_answer = normalize_answer(question.get("answer_key"))
            is_correct = selected == correct_answer
            if is_correct:
                correct_count += 1

            quiz_item_id = None
            if persist:
                cursor = conn.execute(
                    """
                    INSERT INTO quiz_items (quiz_session_id, question_id, sort_order)
                    VALUES (?, ?, ?)
                    """,
                    (quiz_session_id, int(question["question_id"]), quiz_number),
                )
                quiz_item_id = int(cursor.lastrowid)
                conn.execute(
                    """
                    INSERT INTO user_answers (quiz_item_id, user_id, selected_answer, is_correct)
                    VALUES (?, ?, ?, ?)
                    """,
                    (quiz_item_id, user_id, selected or None, 1 if is_correct else 0),
                )

            for code in question.get("knowledge_point_codes", []):
                bucket = weakness.setdefault(
                    code,
                    {"attempted_count": 0, "wrong_count": 0, "question_numbers": []},
                )
                bucket["attempted_count"] += 1
                if not is_correct:
                    bucket["wrong_count"] += 1
                    bucket["question_numbers"].append(quiz_number)

            if not is_correct:
                graded_questions.append(
                    {
                        "quiz_number": quiz_number,
                        "question_id": question["question_id"],
                        "question_type": question["question_type"],
                        "selected_answer": selected,
                        "correct_answer": correct_answer,
                        "knowledge_point_codes": question.get("knowledge_point_codes", []),
                        "source_label": question.get("source", {}).get("label"),
                        "stem": question.get("stem"),
                    }
                )

        total = len(questions)
        accuracy = correct_count / total if total else 0.0

        weakness_rows = []
        for code, bucket in sorted(weakness.items()):
            attempted = int(bucket["attempted_count"])
            wrong = int(bucket["wrong_count"])
            item_accuracy = (attempted - wrong) / attempted if attempted else 0.0
            weakness_rows.append(
                {
                    "knowledge_point_code": code,
                    "attempted_count": attempted,
                    "wrong_count": wrong,
                    "accuracy": round(item_accuracy, 4),
                    "wrong_question_numbers": bucket["question_numbers"],
                }
            )

            if persist and quiz_session_id is not None:
                for knowledge_point_id in knowledge_point_ids(conn, [code]):
                    conn.execute(
                        """
                        INSERT INTO weakness_snapshots (
                          user_id, quiz_session_id, knowledge_point_id,
                          attempted_count, wrong_count, accuracy, ai_summary_zh
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            user_id,
                            quiz_session_id,
                            knowledge_point_id,
                            attempted,
                            wrong,
                            item_accuracy,
                            summary_for_knowledge_point(code, attempted, wrong),
                        ),
                    )

        if persist and quiz_session_id is not None:
            conn.execute(
                """
                UPDATE quiz_sessions
                SET status = 'reviewed',
                    correct_count = ?,
                    accuracy = ?,
                    submitted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (correct_count, accuracy, quiz_session_id),
            )
            conn.commit()
        else:
            conn.rollback()

    report = {
        "quiz_path": str(quiz_path),
        "answers_path": str(answers_path),
        "quiz_session_id": quiz_session_id,
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
        "total_questions": len(questions),
        "answered_count": len([value for value in answers.values() if value]),
        "correct_count": correct_count,
        "wrong_count": len(questions) - correct_count,
        "accuracy": round(accuracy, 4),
        "weakness": weakness_rows,
        "wrong_questions": graded_questions,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def summary_for_knowledge_point(code: str, attempted: int, wrong: int) -> str:
    if attempted == 0:
        return f"{code}: 本次未作答。"
    if wrong == 0:
        return f"{code}: 本次全部答对，保持复习节奏即可。"
    return f"{code}: 本次 {attempted} 题中错 {wrong} 题，建议优先回看错题并补做同类练习。"


def create_answer_template(quiz_path: Path, output_path: Path) -> dict[str, Any]:
    quiz = load_json(quiz_path)
    answers = [
        {
            "quiz_number": question["quiz_number"],
            "question_id": question["question_id"],
            "selected_answer": "",
        }
        for question in quiz.get("questions", [])
    ]
    payload = {"quiz_path": str(quiz_path), "answers": answers}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"output": str(output_path), "answers": len(answers)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Grade a generated TEM8 quiz.")
    parser.add_argument("--quiz", type=Path, required=True)
    parser.add_argument("--answers", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--persist", action="store_true", help="Write quiz session, answers and weakness snapshots to DB.")
    parser.add_argument("--user-id", type=int)
    parser.add_argument("--title")
    parser.add_argument("--create-answer-template", action="store_true")
    args = parser.parse_args()

    if args.create_answer_template:
        output = args.output or DEFAULT_REPORT_DIR / f"{args.quiz.stem}_answers_template.json"
        result = create_answer_template(args.quiz, output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.answers is None:
        raise SystemExit("--answers is required unless --create-answer-template is used.")

    output = args.output or DEFAULT_REPORT_DIR / f"{args.quiz.stem}_report.json"
    result = grade_quiz(
        quiz_path=args.quiz,
        answers_path=args.answers,
        output_path=output,
        persist=args.persist,
        user_id=args.user_id,
        title=args.title,
    )
    print(
        json.dumps(
            {
                "output": str(output),
                "quiz_session_id": result["quiz_session_id"],
                "total_questions": result["total_questions"],
                "correct_count": result["correct_count"],
                "accuracy": result["accuracy"],
                "weakness": result["weakness"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
