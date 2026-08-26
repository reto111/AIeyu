from __future__ import annotations

import argparse
import csv
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
CLEAN_JSON = ROOT / "data" / "processed" / "tem4_review_clean" / "tem4_russian_2024_review.json"
CHECKED_JSON = ROOT / "data" / "processed" / "structured" / "tem4" / "tem4_russian_2024_review_llm_checked.json"
AUDIT_CSV = ROOT / "data" / "processed" / "question_quality" / "tem4" / "tem4_2024_llm_ocr_audit.csv"

# Conservative local-LLM decisions. Stems and passage bodies are not replaced
# because the clean OCR is not uniformly better than the original OCR.
OPTION_REPLACEMENTS = {3, 26, 40}
ANSWER_REPLACEMENTS = {
    66: "D",
    67: "C",
    68: "C",
    69: "B",
    70: "A",
    86: "D",
}


def load_clean_questions(path: Path) -> dict[int, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {int(item["source_question_number"]): item for item in payload["questions"]}


def find_question(conn: sqlite3.Connection, number: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT q.id, q.source_question_number, q.correct_answer, q.review_status
        FROM questions q
        JOIN exam_systems es ON es.id = q.exam_system_id
        WHERE es.code = 'TEM4_RU'
          AND q.source_year = 2024
          AND q.source_question_number = ?
        """,
        (str(number),),
    ).fetchone()
    if row is None:
        raise ValueError(f"Missing TEM4 2024 question {number}.")
    return row


def apply(
    db_path: Path,
    clean_json: Path,
    checked_json: Path,
    audit_csv: Path,
    dry_run: bool,
) -> dict[str, Any]:
    clean = load_clean_questions(clean_json)
    backup_path = db_path.parent.parent / "data" / "processed" / "backups" / (
        "russian_ai_tutor_before_tem4_llm_ocr_review_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".sqlite"
    )
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(db_path, backup_path)

    applied: list[int] = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        for number in sorted(OPTION_REPLACEMENTS | set(ANSWER_REPLACEMENTS)):
            row = find_question(conn, number)
            qid = int(row["id"])
            item = clean[number]
            if number in OPTION_REPLACEMENTS:
                conn.execute("DELETE FROM question_options WHERE question_id = ?", (qid,))
                for sort_order, option in enumerate(item.get("options") or []):
                    conn.execute(
                        """
                        INSERT INTO question_options
                          (question_id, option_key, option_text, sort_order)
                        VALUES (?, ?, ?, ?)
                        """,
                        (qid, option["key"], option.get("text") or "", sort_order),
                    )
            if number in ANSWER_REPLACEMENTS:
                conn.execute(
                    "UPDATE questions SET correct_answer = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (ANSWER_REPLACEMENTS[number], qid),
                )
            conn.execute(
                """
                INSERT INTO question_review_logs
                  (question_id, review_decision, review_notes, reviewer)
                VALUES (?, 'needs_review', ?, 'local_llm_ocr_review')
                """,
                (
                    qid,
                    "watermark_clean_ocr_cross_check; high_confidence_correction; "
                    "keep_needs_review_until_human_approval",
                ),
            )
            applied.append(number)
        if dry_run:
            conn.rollback()
        else:
            conn.commit()

    checked = json.loads(clean_json.read_text(encoding="utf-8"))
    for item in checked["questions"]:
        number = int(item["source_question_number"])
        if number in OPTION_REPLACEMENTS:
            item["review_notes"] = "local_llm_ocr_review: replaced options from watermark-clean OCR; keep pending human review"
        if number in ANSWER_REPLACEMENTS:
            item["correct_answer"] = ANSWER_REPLACEMENTS[number]
            item["review_notes"] = "local_llm_ocr_review: answer cross-checked from clean OCR and question knowledge; keep pending human review"
        item["review_status"] = "needs_review"
    checked_json.parent.mkdir(parents=True, exist_ok=True)
    checked_json.write_text(json.dumps(checked, ensure_ascii=False, indent=2), encoding="utf-8")

    audit_csv.parent.mkdir(parents=True, exist_ok=True)
    with audit_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "source_year",
                "source_question_number",
                "question_type",
                "decision",
                "changed_fields",
                "reason",
                "review_status",
            ],
        )
        writer.writeheader()
        for item in checked["questions"]:
            number = int(item["source_question_number"])
            fields: list[str] = []
            if number in OPTION_REPLACEMENTS:
                fields.append("options")
            if number in ANSWER_REPLACEMENTS:
                fields.append("correct_answer")
            decision = "local_llm_corrected" if fields else "keep_existing"
            reason = (
                "clean OCR removes page watermark and restores a complete 4-option structure"
                if number in OPTION_REPLACEMENTS
                else (
                    "answer is legible in clean OCR and independently consistent with the question"
                    if number in ANSWER_REPLACEMENTS
                    else "clean OCR is not uniformly better; retain existing text for human review"
                )
            )
            writer.writerow(
                {
                    "source_year": 2024,
                    "source_question_number": number,
                    "question_type": item["question_type"],
                    "decision": decision,
                    "changed_fields": ",".join(fields),
                    "reason": reason,
                    "review_status": "needs_review",
                }
            )

    return {
        "db": str(db_path),
        "dry_run": dry_run,
        "backup": str(backup_path),
        "applied_questions": applied,
        "checked_json": str(checked_json),
        "audit_csv": str(audit_csv),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply conservative local-LLM review decisions for TEM4 2024 clean OCR.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--clean-json", type=Path, default=CLEAN_JSON)
    parser.add_argument("--checked-json", type=Path, default=CHECKED_JSON)
    parser.add_argument("--audit-csv", type=Path, default=AUDIT_CSV)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(apply(args.db, args.clean_json, args.checked_json, args.audit_csv, args.dry_run), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()