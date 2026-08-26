from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'database' / 'russian_ai_tutor.sqlite'
TYPE_TO_CODE = {'listening_choice':'listening','grammar_choice':'grammar','culture_choice':'culture','reading_choice':'reading'}


def main() -> None:
    parser=argparse.ArgumentParser(description='Assign TEM4 coarse knowledge points to pending questions.')
    parser.add_argument('--year',type=int,action='append',default=[]); parser.add_argument('--db',type=Path,default=DB_PATH); parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args(); summary:dict[str,int]={}
    with sqlite3.connect(args.db) as conn:
        conn.row_factory=sqlite3.Row; conn.execute('PRAGMA foreign_keys=ON')
        system_id=int(conn.execute("SELECT id FROM exam_systems WHERE code='TEM4_RU'").fetchone()[0])
        points={r['code']:int(r['id']) for r in conn.execute('SELECT code,id FROM knowledge_points WHERE exam_system_id=?',(system_id,)).fetchall()}
        filters=['q.exam_system_id=?','q.review_status=\'needs_review\'','qt.code IN (\'listening_choice\',\'grammar_choice\',\'culture_choice\',\'reading_choice\')']; params:[Any]=[system_id]
        if args.year:
            placeholders=','.join('?' for _ in args.year); filters.append(f'q.source_year IN ({placeholders})'); params.extend(args.year)
        rows=conn.execute(f"SELECT q.id,qt.code FROM questions q JOIN question_types qt ON qt.id=q.question_type_id WHERE {' AND '.join(filters)} AND NOT EXISTS (SELECT 1 FROM question_knowledge_points qkp WHERE qkp.question_id=q.id)",params).fetchall()
        for row in rows:
            code=TYPE_TO_CODE[row['code']]
            if code not in points: raise ValueError(f'Missing TEM4 knowledge point {code}. Run seed_tem4_knowledge_points.py first.')
            conn.execute('INSERT INTO question_knowledge_points(question_id,knowledge_point_id,weight) VALUES(?,?,1.0)',(int(row['id']),points[code])); summary[code]=summary.get(code,0)+1
        if args.dry_run: conn.rollback()
        else: conn.commit()
    print(json.dumps({'exam_system':'TEM4_RU','years':args.year or 'all','dry_run':args.dry_run,'assigned_total':sum(summary.values()),'assigned_by_knowledge':summary},ensure_ascii=False,indent=2))


if __name__=='__main__': main()
