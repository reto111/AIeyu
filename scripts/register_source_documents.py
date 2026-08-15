from __future__ import annotations

import json
import re
import sqlite3
import argparse
from pathlib import Path


DB_PATH = Path("database/russian_ai_tutor.sqlite")
RAW_DIR = Path("data/raw_pdfs")
PROCESSED_DIR = Path("data/processed")
INVENTORY_PATH = PROCESSED_DIR / "pdf_inventory.json"


def read_text_sample(pdf_path: Path, max_chars: int = 5000) -> str:
    text_path = PROCESSED_DIR / f"{pdf_path.stem}.txt"
    if not text_path.exists():
        return ""
    return text_path.read_text(encoding="utf-8", errors="replace")[:max_chars]


def ensure_exam_seed(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO exam_systems (code, name_zh, name_original, description)
        VALUES (?, ?, ?, ?)
        """,
        ("TEM8_RU", "俄语专业八级", "Русский язык TEM-8", "第一阶段默认考试体系"),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO exam_systems (code, name_zh, name_original, description)
        VALUES (?, ?, ?, ?)
        """,
        ("TEM4_RU", "俄语专业四级", "Русский язык TEM-4", "当前资料中已出现专四真题"),
    )

    for system_code, level_code, level_name in [
        ("TEM8_RU", "TEM8", "专八"),
        ("TEM4_RU", "TEM4", "专四"),
    ]:
        system_id = conn.execute(
            "SELECT id FROM exam_systems WHERE code = ?", (system_code,)
        ).fetchone()[0]
        conn.execute(
            """
            INSERT OR IGNORE INTO exam_levels (exam_system_id, code, name_zh, sort_order)
            VALUES (?, ?, ?, 1)
            """,
            (system_id, level_code, level_name),
        )


def detect_exam_system(pdf_path: Path, text_sample: str) -> tuple[str, str]:
    compact = re.sub(r"\s+", "", text_sample)

    if "专业四级" in compact:
        return "TEM4_RU", "detected_from_text"
    if "专业八级" in compact or "八级" in compact:
        return "TEM8_RU", "detected_from_text"

    if "tem4" in pdf_path.name.lower():
        return "TEM4_RU", "inferred_from_filename"
    if "tem8" in pdf_path.name.lower():
        return "TEM8_RU", "inferred_from_filename"

    return "TEM8_RU", "fallback_needs_review"


def detect_document_type(pdf_path: Path, text_sample: str) -> str:
    name = pdf_path.name.lower()
    compact = re.sub(r"\s+", "", text_sample)

    if "questions" in name:
        return "questions"
    if "answers" in name:
        return "answers"
    if "详解" in compact or "解析" in compact:
        return "analysis"
    if "full" in name:
        return "full"
    return "full"


def detect_year(pdf_path: Path, text_sample: str) -> int | None:
    match = re.search(r"(20\d{2})", pdf_path.name)
    if match:
        return int(match.group(1))
    match = re.search(r"(20\d{2})", text_sample)
    if match:
        return int(match.group(1))
    return None


def get_inventory_by_name() -> dict[str, dict]:
    if not INVENTORY_PATH.exists():
        return {}
    items = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    return {item["file_name"]: item for item in items}


def upsert_source_document(
    conn: sqlite3.Connection,
    pdf_path: Path,
    inventory: dict,
    include_non_tem8: bool,
) -> bool:
    text_sample = read_text_sample(pdf_path)
    exam_code, exam_detection = detect_exam_system(pdf_path, text_sample)
    document_type = detect_document_type(pdf_path, text_sample)
    source_year = detect_year(pdf_path, text_sample)

    if exam_code != "TEM8_RU" and not include_non_tem8:
        print(f"Skipping non-TEM8 source: {pdf_path.name} ({exam_code}, {exam_detection})")
        return False

    exam_system_id = conn.execute(
        "SELECT id FROM exam_systems WHERE code = ?", (exam_code,)
    ).fetchone()[0]
    level_id = conn.execute(
        "SELECT id FROM exam_levels WHERE exam_system_id = ? ORDER BY sort_order LIMIT 1",
        (exam_system_id,),
    ).fetchone()[0]

    text_status = "extracted"
    if inventory.get("classification") == "scanned_or_photo_pdf":
        text_status = "extracted"
    if inventory.get("classification") == "locked":
        text_status = "pending"

    notes = {
        "classification": inventory.get("classification"),
        "encrypted": inventory.get("encrypted"),
        "authenticated": inventory.get("authenticated"),
        "exam_detection": exam_detection,
        "needs_exam_confirmation": exam_detection != "detected_from_text",
    }

    title = f"{source_year or 'Unknown'} {exam_code} {document_type} - {pdf_path.name}"
    file_path = str(pdf_path).replace("\\", "/")
    existing = conn.execute(
        "SELECT id FROM source_documents WHERE file_path = ?", (file_path,)
    ).fetchone()

    values = (
        exam_system_id,
        level_id,
        source_year,
        title,
        document_type,
        file_path,
        text_status,
        "pending",
        json.dumps(notes, ensure_ascii=False),
    )

    if existing:
        conn.execute(
            """
            UPDATE source_documents
            SET exam_system_id = ?, level_id = ?, source_year = ?, title = ?,
                document_type = ?, text_extract_status = ?, review_status = ?,
                notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                exam_system_id,
                level_id,
                source_year,
                title,
                document_type,
                text_status,
                "pending",
                json.dumps(notes, ensure_ascii=False),
                existing[0],
            ),
        )
    else:
        conn.execute(
            """
            INSERT INTO source_documents (
              exam_system_id, level_id, source_year, title, document_type,
              file_path, text_extract_status, review_status, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Register raw PDF files as source documents.")
    parser.add_argument(
        "--include-non-tem8",
        action="store_true",
        help="Register PDFs detected as non-TEM8. Default is to skip them.",
    )
    parser.add_argument(
        "--reset-sources",
        action="store_true",
        help="Delete existing source_documents before registering current raw PDFs.",
    )
    args = parser.parse_args()

    inventory_by_name = get_inventory_by_name()
    pdfs = sorted(RAW_DIR.glob("*.pdf"))

    with sqlite3.connect(DB_PATH) as conn:
        ensure_exam_seed(conn)
        if args.reset_sources:
            conn.execute("DELETE FROM source_documents")
        for pdf_path in pdfs:
            upsert_source_document(
                conn,
                pdf_path,
                inventory_by_name.get(pdf_path.name, {}),
                include_non_tem8=args.include_non_tem8,
            )
        conn.commit()

        rows = conn.execute(
            """
            SELECT sd.source_year, es.code, sd.document_type, sd.text_extract_status,
                   sd.review_status, sd.file_path
            FROM source_documents sd
            JOIN exam_systems es ON es.id = sd.exam_system_id
            ORDER BY sd.source_year, sd.file_path
            """
        ).fetchall()

    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
