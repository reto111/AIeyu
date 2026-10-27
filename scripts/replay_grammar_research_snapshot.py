"""Replay a frozen retrieval evaluation from verified data, without PDF I/O.

This checks package and page-record integrity. It does not independently check
the scan or generate an answer; archived source paths remain reference metadata.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode=True

import argparse
from contextlib import closing
from datetime import datetime,timezone
import json
from pathlib import Path
import sqlite3

from export_grammar_research_snapshot import verify_package
from grammar_reference import dump,file_sha256
from grammar_question_search import search_question
from grammar_rag import section_snapshot,text_hash


def replay(snapshot,cases_path,output):
    snapshot,cases_path,output=Path(snapshot).resolve(),Path(cases_path),Path(output).resolve()
    if output.is_relative_to(snapshot) or output.exists():
        raise ValueError('Replay output must be a new file outside the immutable package')
    verify_package(snapshot)
    manifest=json.loads((snapshot/'manifest.json').read_text(encoding='utf8'))
    frozen=json.loads(cases_path.read_text(encoding='utf8'))
    scripts=Path(__file__).resolve().parent
    if manifest['input_database_sha256']!=frozen['database_sha256']:
        raise ValueError('Frozen cases do not bind to snapshot source')
    if frozen['implementation_sha256']!=file_sha256(scripts/'grammar_question_search.py') or frozen['rag_implementation_sha256']!=file_sha256(scripts/'grammar_rag.py'):
        raise ValueError('Core implementation differs from frozen cases')
    db=snapshot/'grammar_reference.sqlite'
    records=[]
    with closing(sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)) as conn:
        conn.row_factory=sqlite3.Row
        source=dict(conn.execute('SELECT * FROM source WHERE id=1').fetchone())
        for case in frozen['cases']:
            for gold in case['gold_sources']:
                row=conn.execute('SELECT * FROM chunks WHERE code=?',(gold['code'],)).fetchone()
                if row is None or row['status']!=gold['status'] or text_hash(row['body'])!=gold['body_sha256']:
                    raise ValueError('Frozen target source changed')
            matches,terms=search_question(case['question'],limit=frozen['limit'],db=db)
            sources,omitted,used=[],[],0
            for match in matches:
                item=section_snapshot(conn,match['code'],source)
                size=len(item['body'])
                if used+size>frozen['max_context_chars']:
                    omitted.append(dict(code=item['code'],reason='whole_section_exceeds_budget',characters=size))
                    continue
                used+=size
                sources.append(dict(source_id=f'G{len(sources)+1}',**item))
            records.append(dict(case_id=case['case_id'],raw_codes=[x['code'] for x in matches],terms=terms,
                prepared_codes=[x['code'] for x in sources],sources=sources,omitted_sections=omitted,context_characters=used))
    result=dict(replayed_at=datetime.now(timezone.utc).isoformat(),snapshot_manifest_sha256=file_sha256(snapshot/'manifest.json'),
        cases_sha256=file_sha256(cases_path),implementation_sha256=frozen['implementation_sha256'],
        replay_script_sha256=file_sha256(Path(__file__)),records=records,external_api_calls=0,pdf_files_opened=0,
        verification_mode='verified_package_and_page_evidence_only',
        limits='仅从已核验快照复现检索与完整节预算，不重新核验原PDF、转录正确性或生成答案。source_path是原归档定位信息，不表示本次读取过该文件。')
    dump(output,result)
    return dict(artifact=str(output),cases=len(records),pdf_files_opened=0,external_api_calls=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',required=True)
    parser.add_argument('--cases',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(replay(args.snapshot,args.cases,args.output),ensure_ascii=False))
