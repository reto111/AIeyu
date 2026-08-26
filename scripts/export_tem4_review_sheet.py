from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'database' / 'russian_ai_tutor.sqlite'
DEFAULT_OUT = ROOT / 'data' / 'processed' / 'review_sheets' / 'tem4_questions_review.csv'
DEFAULT_PASSAGES = ROOT / 'data' / 'processed' / 'review_sheets' / 'tem4_passages_review.csv'
FIELDS = ['question_id','source_year','source_question_number','source_label','question_type','review_status','stem','option_a','option_b','option_c','option_d','correct_answer','explanation_zh','passage_id','passage_title','knowledge_point_codes','review_decision','review_notes']
PASSAGE_FIELDS = ['passage_id','source_year','source_label','passage_title','passage_body','review_notes']


def cell(value: Any) -> str:
    text = '' if value is None else str(value).replace('\r\n','\n').replace('\r','\n').strip()
    return "'" + text if text.startswith(('=','+','-','@')) else text


def export(out: Path, passages_out: Path, db_path: Path) -> dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        questions = conn.execute(
            """SELECT q.*, qt.code AS question_type, p.title AS passage_title
               FROM questions q JOIN exam_systems es ON es.id=q.exam_system_id
               JOIN question_types qt ON qt.id=q.question_type_id LEFT JOIN passages p ON p.id=q.passage_id
               WHERE es.code='TEM4_RU' AND q.review_status='needs_review'
               ORDER BY q.source_year, CAST(q.source_question_number AS INTEGER), q.id"""
        ).fetchall()
        rows = []
        for q in questions:
            opts = {str(r['option_key']).upper(): r['option_text'] for r in conn.execute('SELECT option_key,option_text FROM question_options WHERE question_id=? ORDER BY sort_order', (q['id'],)).fetchall()}
            codes = [r[0] for r in conn.execute('SELECT kp.code FROM question_knowledge_points qkp JOIN knowledge_points kp ON kp.id=qkp.knowledge_point_id WHERE qkp.question_id=? ORDER BY kp.sort_order,kp.code', (q['id'],)).fetchall()]
            rows.append({'question_id':cell(q['id']),'source_year':cell(q['source_year']),'source_question_number':cell(q['source_question_number']),'source_label':cell(q['source_label']),'question_type':cell(q['question_type']),'review_status':cell(q['review_status']),'stem':cell(q['stem']),'option_a':cell(opts.get('A')),'option_b':cell(opts.get('B')),'option_c':cell(opts.get('C')),'option_d':cell(opts.get('D')),'correct_answer':cell(q['correct_answer']),'explanation_zh':cell(q['explanation_zh']),'passage_id':cell(q['passage_id']),'passage_title':cell(q['passage_title']),'knowledge_point_codes':cell(','.join(codes)),'review_decision':'','review_notes':''})
        passages = conn.execute(
            """SELECT DISTINCT p.id AS passage_id,q.source_year,q.source_label,p.title AS passage_title,p.body AS passage_body
               FROM questions q JOIN exam_systems es ON es.id=q.exam_system_id JOIN passages p ON p.id=q.passage_id
               WHERE es.code='TEM4_RU' AND q.review_status='needs_review' ORDER BY q.source_year,p.id"""
        ).fetchall()
        passage_rows = [{'passage_id':cell(p['passage_id']),'source_year':cell(p['source_year']),'source_label':cell(p['source_label']),'passage_title':cell(p['passage_title']),'passage_body':cell(p['passage_body']),'review_notes':''} for p in passages]
    out.parent.mkdir(parents=True, exist_ok=True); passages_out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS); writer.writeheader(); writer.writerows(rows)
    with passages_out.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=PASSAGE_FIELDS); writer.writeheader(); writer.writerows(passage_rows)
    return {'questions_output':str(out),'question_rows':len(rows),'passages_output':str(passages_out),'passage_rows':len(passage_rows),'exam_system':'TEM4_RU'}


def main() -> None:
    parser=argparse.ArgumentParser(description='Export TEM4-only pending review sheets.')
    parser.add_argument('--output',type=Path,default=DEFAULT_OUT); parser.add_argument('--passages-output',type=Path,default=DEFAULT_PASSAGES); parser.add_argument('--db',type=Path,default=DB_PATH)
    args=parser.parse_args(); print(json.dumps(export(args.output,args.passages_output,args.db),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
