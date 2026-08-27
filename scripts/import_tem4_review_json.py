from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'database' / 'russian_ai_tutor.sqlite'


def fetch_id(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> int:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise ValueError(f'Missing database row: {sql} {params}')
    return int(row[0])


def source_document_id(conn: sqlite3.Connection, year: int) -> int:
    row = conn.execute(
        """SELECT sd.id FROM source_documents sd JOIN exam_systems es ON es.id=sd.exam_system_id
           WHERE es.code='TEM4_RU' AND sd.source_year=? AND sd.document_type IN ('full','questions')
           ORDER BY CASE sd.document_type WHEN 'full' THEN 0 ELSE 1 END, sd.id LIMIT 1""",
        (year,),
    ).fetchone()
    if row is None:
        raise ValueError(f'No TEM4 full/questions source document found for {year}. Run register_tem4_pdfs.py first.')
    return int(row[0])


def get_or_create_passage(conn: sqlite3.Connection, source_id: int, payload: dict[str, Any] | None, cache: dict[tuple[str, str], int]) -> int | None:
    if not payload:
        return None
    title = str(payload.get('title') or '')
    body = str(payload.get('body') or '')
    if not body:
        return None
    key = (title, body)
    if key in cache:
        return cache[key]
    existing = conn.execute('SELECT id FROM passages WHERE source_document_id=? AND COALESCE(title,\'\')=? AND body=?', (source_id, title, body)).fetchone()
    if existing:
        passage_id = int(existing[0])
    else:
        passage_id = int(conn.execute("INSERT INTO passages (source_document_id,title,body,language) VALUES (?,?,?,'ru')", (source_id,title,body)).lastrowid)
    cache[key] = passage_id
    return passage_id


def insert_one(conn: sqlite3.Connection, question: dict[str, Any], system_id: int, level_id: int, source_id: int, passage_id: int | None) -> int:
    type_id = fetch_id(conn, 'SELECT id FROM question_types WHERE code=?', (question['question_type'],))
    qid = int(conn.execute(
        """INSERT INTO questions (exam_system_id,level_id,question_type_id,passage_id,source_document_id,source_year,source_question_number,
           stem,correct_answer,explanation_zh,difficulty,review_status,generation_status,source_page,raw_text,source_usage,content_origin,
           source_label,requires_source_label,similarity_review_status)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (system_id,level_id,type_id,passage_id,source_id,question.get('source_year'),question.get('source_question_number'),question.get('stem') or '',
         question.get('correct_answer'),question.get('explanation_zh'),question.get('difficulty'),'needs_review','human_imported',question.get('source_page'),
         question.get('raw_text'),'practice','past_exam_original',question.get('source_label'),1,'not_checked'),
    ).lastrowid)
    for index, option in enumerate(question.get('options', [])):
        conn.execute('INSERT INTO question_options (question_id,option_key,option_text,sort_order) VALUES (?,?,?,?)', (qid,option.get('key'),option.get('text') or '',index))
    return qid


def import_file(conn: sqlite3.Connection, path: Path, excluded_types: set[str]) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    year = int(payload['source_year'])
    source_id = source_document_id(conn, year)
    system_id = fetch_id(conn, "SELECT id FROM exam_systems WHERE code='TEM4_RU'", ())
    level_id = fetch_id(conn, "SELECT id FROM exam_levels WHERE exam_system_id=? AND code='TEM4'", (system_id,))
    cache: dict[tuple[str, str], int] = {}
    inserted = 0
    skipped = 0
    excluded = 0
    for question in payload.get('questions', []):
        if question.get('question_type') in excluded_types:
            excluded += 1
            continue
        existing = conn.execute("SELECT id FROM questions WHERE source_document_id=? AND source_question_number=? AND content_origin='past_exam_original'", (source_id,question.get('source_question_number'))).fetchone()
        if existing:
            skipped += 1
            continue
        passage_id = get_or_create_passage(conn, source_id, question.get('passage'), cache)
        insert_one(conn, question, system_id, level_id, source_id, passage_id)
        inserted += 1
    return {'file': str(path), 'source_year': year, 'inserted': inserted, 'skipped_existing': skipped, 'excluded': excluded}


def main() -> None:
    parser = argparse.ArgumentParser(description='Import TEM4 review JSON into TEM4-only SQLite rows.')
    parser.add_argument('paths', nargs='+', type=Path)
    parser.add_argument('--db', type=Path, default=DB_PATH)
    parser.add_argument('--exclude-question-type', action='append', default=[], help='Question type code to keep out of the database; repeatable.')
    args = parser.parse_args()
    excluded_types = set(args.exclude_question_type)
    with sqlite3.connect(args.db) as conn:
        conn.execute('PRAGMA foreign_keys = ON')
        results = [import_file(conn, path, excluded_types) for path in args.paths]
        conn.commit()
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
