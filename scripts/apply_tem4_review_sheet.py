from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'database' / 'russian_ai_tutor.sqlite'
VALID = {'approved','needs_review','needs_fix','rejected'}
STATUS = {'approved':'approved','needs_review':'needs_review','needs_fix':'needs_review','rejected':'rejected'}


def norm(value: str | None) -> str:
    return (value or '').strip().lstrip('\ufeff')


def codes(value: str | None) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in norm(value).replace(';',',').split(',') if item.strip()))


def apply(path: Path, db_path: Path, reviewer: str, dry_run: bool) -> dict[str, Any]:
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    summary: dict[str,int] = {}
    with sqlite3.connect(db_path) as conn:
        conn.row_factory=sqlite3.Row; conn.execute('PRAGMA foreign_keys = ON')
        system_id=int(conn.execute("SELECT id FROM exam_systems WHERE code='TEM4_RU'").fetchone()[0])
        for row in rows:
            raw_id=norm(row.get('question_id'))
            if not raw_id:
                summary['skipped_blank_question_id']=summary.get('skipped_blank_question_id',0)+1; continue
            qid=int(raw_id)
            question=conn.execute('SELECT id FROM questions WHERE id=? AND exam_system_id=?',(qid,system_id)).fetchone()
            if question is None: raise ValueError(f'Question {qid} is not a TEM4 question.')
            decision=norm(row.get('review_decision'))
            if not decision:
                summary['skipped_blank_decision']=summary.get('skipped_blank_decision',0)+1; continue
            if decision not in VALID: raise ValueError(f'Invalid decision for TEM4 question {qid}: {decision}')
            point_codes=codes(row.get('knowledge_point_codes'))
            if decision=='approved' and not point_codes: raise ValueError(f'Approved TEM4 question {qid} needs knowledge_point_codes.')
            point_ids={r['code']:int(r['id']) for r in conn.execute('SELECT code,id FROM knowledge_points WHERE exam_system_id=?',(system_id,)).fetchall()}
            missing=sorted(set(point_codes)-set(point_ids))
            if missing: raise ValueError(f'Unknown TEM4 knowledge point(s): {", ".join(missing)}')
            if point_codes:
                conn.execute('DELETE FROM question_knowledge_points WHERE question_id=?',(qid,))
                conn.executemany('INSERT INTO question_knowledge_points (question_id,knowledge_point_id,weight) VALUES (?, ?, 1.0)',[(qid,point_ids[code]) for code in point_codes])
            conn.execute('UPDATE questions SET review_status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?',(STATUS[decision],qid))
            conn.execute('INSERT INTO question_review_logs (question_id,review_decision,review_notes,knowledge_point_codes,reviewer) VALUES (?,?,?,?,?)',(qid,decision,norm(row.get('review_notes')) or None,','.join(point_codes) or None,reviewer))
            key='applied_'+decision; summary[key]=summary.get(key,0)+1
        if dry_run: conn.rollback()
        else: conn.commit()
    return {'input':str(path),'exam_system':'TEM4_RU','dry_run':dry_run,'summary':summary}


def main() -> None:
    parser=argparse.ArgumentParser(description='Apply a TEM4 review sheet with TEM4-only knowledge points.')
    parser.add_argument('--input',type=Path,required=True); parser.add_argument('--db',type=Path,default=DB_PATH); parser.add_argument('--reviewer',default='manual_review'); parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args(); print(json.dumps(apply(args.input,args.db,args.reviewer,args.dry_run),ensure_ascii=False,indent=2))


if __name__=='__main__': main()
