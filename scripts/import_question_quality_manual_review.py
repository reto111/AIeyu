from __future__ import annotations

import argparse
import csv
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
REVIEW_CSV = ROOT / "data" / "processed" / "question_quality" / "question_quality_manual_review_context.csv"
OUT_DIR = ROOT / "data" / "processed" / "question_quality"
BACKUP_DIR = ROOT / "data" / "processed" / "backups"
REVIEWER = "manual_quality_review_import"

EXPECTED_ANSWERS = {"A", "B", "C", "D"}
NOISE_RE = re.compile(r"(N\\A|СТРАНОВЕДЕНИЕ|ЛИТЕРАТУРА|ПЕРЕВОД|HAVE|Hi\. WE|ti\.|[{}[\]<>@#$^&*+=~`|\\])", re.I)

TEXT_FIXES = {
    "пренадлежит": "принадлежит",
    "A.Н.": "А.Н.",
    "выитй": "выйти",
    "Ha работу": "на работу",
    "внутренни дел": "внутренних дел",
    "отнесность": "отнестись",
    "овместное": "совместное",
    "струга": "супруга",
    "любовь А брака": "любовью и браком",
    "встунления": "вступления",
    "слимком": "слишком",
    "соответствуе содержанию": "соответствует содержанию",
    "бы введей": "был введен",
    "передвинкть": "передвинуть",
    "то ли...то ли... м}": "то ли..., то ли...",
    "«Путешествие из Петербурга в Москву» СТРАНОВЕДЕНИЕ": "«Путешествие из Петербурга в Москву»",
    "Лучше научить противника не иметь в жизни серьёзных конфликтов. =\" \\ Hi. WE (Перевод. 20% ы минут) 1.": "Лучше научить противника не иметь в жизни серьёзных конфликтов.",
    "Лучше научить противника не иметь в жизни серьёзных конфликтов. \" Hi. WE (Перевод. 20% ы минут) 1.": "Лучше научить противника не иметь в жизни серьёзных конфликтов.",
    "Россияне предпочитают сначала встать на ноги, а потом заводить семью. ti. HAVE (Перевод. 20 баллов, 45 минут) 1.": "Россияне предпочитают сначала встать на ноги, а потом заводить семью.",
}


def normalize_text(value: str | None) -> str:
    text = (value or "").strip()
    text = text.replace("__", "____")
    text = text.replace(" .", ".")
    text = text.replace(" ,", ",")
    text = text.replace("‚", ",")
    text = text.replace("“", "")
    text = text.replace("„", "")
    text = text.replace("`", "")
    text = text.replace("\\", "")
    text = text.replace("|", "")
    text = text.replace("=", "")
    text = re.sub(r"\s+", " ", text)
    for old, new in TEXT_FIXES.items():
        text = text.replace(old, new)
    text = re.sub(r"\s+([,.?!:;])", r"\1", text)
    text = re.sub(r"____\s+\.", "____.", text)
    return text.strip()


def normalize_row(row: dict) -> dict:
    row = dict(row)
    if not row.get("correct_answer") and (row.get("passage_length") or "").strip().upper() in EXPECTED_ANSWERS:
        row["correct_answer"] = row["passage_length"].strip().upper()
        row["passage_length"] = row.get("manual_decision") or ""
        row["manual_decision"] = ""
    row["correct_answer"] = (row.get("correct_answer") or "").strip().upper()
    for key in ["stem", "A", "B", "C", "D"]:
        row[key] = normalize_text(row.get(key))
    return row


def validate_row(row: dict) -> list[str]:
    errors: list[str] = []
    if not (row.get("question_id") or "").isdigit():
        errors.append("question_id_missing")
    if not row.get("stem"):
        errors.append("stem_missing")
    for key in ["A", "B", "C", "D"]:
        if not row.get(key):
            errors.append(f"option_{key}_missing")
    if row.get("correct_answer") not in EXPECTED_ANSWERS:
        errors.append("correct_answer_invalid")
    visible_text = " ".join(row.get(key, "") for key in ["stem", "A", "B", "C", "D"])
    if NOISE_RE.search(visible_text):
        errors.append("visible_ocr_noise_remaining")
    if "____" not in row.get("stem", "") and row.get("type_code") in {"grammar_choice", "literature_choice", "culture_choice"}:
        errors.append("blank_marker_missing")
    return errors


def add_log(con: sqlite3.Connection, question_id: int, decision: str, note: str) -> None:
    con.execute(
        """
        insert into question_review_logs
          (question_id, review_decision, review_notes, knowledge_point_codes, reviewer)
        values (?, ?, ?, NULL, ?)
        """,
        (question_id, decision, note, REVIEWER),
    )


def backup_db(db_path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{db_path.stem}_before_manual_quality_import_{stamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def import_rows(con: sqlite3.Connection, rows: list[dict]) -> tuple[list[dict], list[dict]]:
    imported: list[dict] = []
    rejected: list[dict] = []
    for original_row in rows:
        row = normalize_row(original_row)
        errors = validate_row(row)
        if errors:
            row["validation_errors"] = ",".join(errors)
            rejected.append(row)
            continue

        question_id = int(row["question_id"])
        con.execute(
            """
            update questions
            set stem = ?,
                correct_answer = ?,
                review_status = 'approved',
                source_usage = 'practice',
                updated_at = CURRENT_TIMESTAMP
            where id = ?
            """,
            (row["stem"], row["correct_answer"], question_id),
        )
        for key in ["A", "B", "C", "D"]:
            con.execute(
                """
                update question_options
                set option_text = ?, updated_at = CURRENT_TIMESTAMP
                where question_id = ? and option_key = ?
                """,
                (row[key], question_id, key),
            )
        add_log(con, question_id, "approved", "imported from manual question quality review table")
        row["validation_errors"] = ""
        imported.append(row)
    return imported, rejected


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "question_id",
        "source_year",
        "source_question_number",
        "type_code",
        "stem",
        "A",
        "B",
        "C",
        "D",
        "correct_answer",
        "validation_errors",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import corrected question quality manual review rows.")
    parser.add_argument("--csv", default=str(REVIEW_CSV), help="Manual review CSV path.")
    parser.add_argument("--db", default=str(DB_PATH), help="SQLite database path.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and export reports without changing DB.")
    args = parser.parse_args()

    with Path(args.csv).open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row

    if args.dry_run:
        imported, rejected = import_rows(sqlite3.connect(":memory:"), [])  # placeholder for types
        imported = []
        rejected = []
        for original_row in rows:
            row = normalize_row(original_row)
            errors = validate_row(row)
            row["validation_errors"] = ",".join(errors)
            if errors:
                rejected.append(row)
            else:
                imported.append(row)
    else:
        backup_path = backup_db(Path(args.db))
        print(f"backup={backup_path}")
        with con:
            imported, rejected = import_rows(con, rows)

    write_rows(OUT_DIR / "question_quality_manual_imported.csv", imported)
    write_rows(OUT_DIR / "question_quality_manual_import_rejected.csv", rejected)
    print(f"importable={len(imported)}")
    print(f"rejected={len(rejected)}")
    print(f"imported_report={OUT_DIR / 'question_quality_manual_imported.csv'}")
    print(f"rejected_report={OUT_DIR / 'question_quality_manual_import_rejected.csv'}")


if __name__ == "__main__":
    main()
