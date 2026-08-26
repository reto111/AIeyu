from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'database' / 'russian_ai_tutor.sqlite'
DEFAULT_RAW_DIR = ROOT / 'data' / 'raw_pdfs' / 'tem4'
DEFAULT_INVENTORY = ROOT / 'data' / 'processed' / 'tem4_pdf_inventory.json'
DEFAULT_TEXT_DIR = ROOT / 'data' / 'processed' / 'tem4_text'


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_exam_seed(conn: sqlite3.Connection) -> tuple[int, int]:
    conn.execute(
        """INSERT OR IGNORE INTO exam_systems (code, name_zh, name_original, description)
           VALUES ('TEM4_RU', '俄语专业四级', 'Русский язык TEM-4', '俄语专四题库')"""
    )
    system_id = int(conn.execute("SELECT id FROM exam_systems WHERE code = 'TEM4_RU'").fetchone()[0])
    conn.execute(
        """INSERT OR IGNORE INTO exam_levels (exam_system_id, code, name_zh, sort_order)
           VALUES (?, 'TEM4', '专四', 1)""",
        (system_id,),
    )
    level_id = int(conn.execute(
        "SELECT id FROM exam_levels WHERE exam_system_id = ? AND code = 'TEM4'", (system_id,)
    ).fetchone()[0])
    return system_id, level_id


def document_type(path: Path) -> str:
    name = path.name.lower()
    if 'answers' in name:
        return 'answers'
    if 'questions' in name:
        return 'questions'
    return 'full'


def source_year(path: Path) -> int | None:
    match = re.search(r'(20\d{2})', path.name)
    return int(match.group(1)) if match else None


def register(path: Path, inventory: dict, text_dir: Path, conn: sqlite3.Connection, system_id: int, level_id: int) -> None:
    year = source_year(path)
    text_path = text_dir / f'{path.stem}.txt'
    notes = {
        'exam_detection': 'tem4_directory_and_filename',
        'ocr_text_path': str(text_path).replace('\\', '/') if text_path.exists() else None,
        'pdf_classification': inventory.get('classification'),
        'encrypted': inventory.get('encrypted'),
        'authenticated': inventory.get('authenticated'),
        'supported_modules': ['listening_choice', 'grammar_choice', 'culture_choice', 'reading_choice'],
        'excluded_module': 'cloze_61_70_or_71_80_until_a_dedicated_question_type_exists',
    }
    file_path = str(path).replace('\\', '/')
    values = (
        system_id, level_id, year,
        f'{year or "Unknown"} 俄语专四 {document_type(path)} - {path.name}',
        document_type(path), file_path, sha256(path),
        'extracted' if text_path.exists() else 'needs_ocr', 'pending',
        json.dumps(notes, ensure_ascii=False),
    )
    existing = conn.execute('SELECT id FROM source_documents WHERE file_path = ?', (file_path,)).fetchone()
    if existing:
        conn.execute(
            """UPDATE source_documents SET exam_system_id=?, level_id=?, source_year=?, title=?,
               document_type=?, file_hash=?, text_extract_status=?, review_status=?, notes=?,
               updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (*values, int(existing[0])),
        )
    else:
        conn.execute(
            """INSERT INTO source_documents (
               exam_system_id, level_id, source_year, title, document_type, file_path,
               file_hash, text_extract_status, review_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            values,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description='Register TEM4 PDFs without touching TEM8 sources.')
    parser.add_argument('--raw-dir', type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument('--inventory', type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument('--text-dir', type=Path, default=DEFAULT_TEXT_DIR)
    parser.add_argument('--db', type=Path, default=DB_PATH)
    args = parser.parse_args()
    inventory_rows = json.loads(args.inventory.read_text(encoding='utf-8')) if args.inventory.exists() else []
    inventory = {item.get('file_name'): item for item in inventory_rows}
    pdfs = sorted(args.raw_dir.glob('*.pdf'))
    if not pdfs:
        raise SystemExit(f'No TEM4 PDFs found in {args.raw_dir}')
    with sqlite3.connect(args.db) as conn:
        conn.execute('PRAGMA foreign_keys = ON')
        system_id, level_id = ensure_exam_seed(conn)
        for path in pdfs:
            register(path, inventory.get(path.name, {}), args.text_dir, conn, system_id, level_id)
        conn.commit()
        rows = conn.execute(
            """SELECT sd.source_year, sd.document_type, sd.file_path, sd.text_extract_status
               FROM source_documents sd JOIN exam_systems es ON es.id=sd.exam_system_id
               WHERE es.code='TEM4_RU' ORDER BY sd.source_year, sd.file_path"""
        ).fetchall()
    print(json.dumps({'exam_system': 'TEM4_RU', 'pdf_count': len(pdfs), 'sources': [dict(zip(['year','document_type','file_path','text_status'], row)) for row in rows]}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
