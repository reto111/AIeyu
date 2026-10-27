"""Run pre-frozen local retrieval cases without changing ranking or source data."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
from contextlib import closing

sys.dont_write_bytecode = True

from grammar_reference import DB, file_sha256, dump
from grammar_question_search import search_question
from grammar_rag import prepare, text_hash


def evaluate(cases_path, output, *, db=DB, snapshot=None):
    cases_path, output, db = Path(cases_path), Path(output), Path(db)
    if output.exists():
        raise FileExistsError('Evaluation artifacts are immutable; choose a new output name')
    frozen = json.loads(cases_path.read_text(encoding='utf8'))
    source_hash = file_sha256(db)
    bound_snapshot = None
    if snapshot is not None:
        from export_grammar_research_snapshot import verify_package
        snapshot = Path(snapshot).resolve()
        verify_package(snapshot)
        binding = json.loads((snapshot/'manifest.json').read_text(encoding='utf8'))
        if binding['input_database_sha256'] != frozen['database_sha256'] or db.resolve() != snapshot/'grammar_reference.sqlite':
            raise ValueError('Snapshot does not bind this database to frozen source')
        bound_snapshot = file_sha256(snapshot/'manifest.json')
    if frozen['database_sha256'] != source_hash and bound_snapshot is None:
        raise ValueError('Database differs from frozen cases')
    code = Path(__file__).resolve().parent
    if frozen['implementation_sha256'] != file_sha256(code/'grammar_question_search.py') or frozen['rag_implementation_sha256'] != file_sha256(code/'grammar_rag.py'):
        raise ValueError('Retrieval implementation changed since cases were frozen')
    identifiers = [x['case_id'] for x in frozen['cases']]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError('Duplicate case identifiers')
    with closing(sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        for case in frozen['cases']:
            for gold in case['gold_sources']:
                row = conn.execute('SELECT * FROM chunks WHERE code=?',(gold['code'],)).fetchone()
                if row is None or row['status'] != gold['status'] or text_hash(row['body']) != gold['body_sha256']:
                    raise ValueError('Frozen gold source changed')
    records = []
    for case in frozen['cases']:
        matches, terms = search_question(case['question'],limit=frozen['limit'],db=db)
        packet = prepare(case['question'],limit=frozen['limit'],max_context_chars=frozen['max_context_chars'],db=db)
        raw = [x['code'] for x in matches]
        actual = [x['code'] for x in packet['sources']]
        expected = case['expected_codes']
        forbidden = set(case['forbidden_codes'])
        records.append(dict(case_id=case['case_id'],kind=case['kind'],question=case['question'],
            expected_codes=expected,raw_codes=raw,prepared_codes=actual,terms=terms,
            raw_target_ranks={x:raw.index(x)+1 if x in raw else None for x in expected},
            raw_target_hits=sum(x in raw for x in expected),prepared_target_hits=sum(x in actual for x in expected),
            forbidden_leaks=sorted(forbidden & set(raw+actual)),packet=packet,
            answer_quality='not_evaluated_no_generation_model_called'))
    if file_sha256(db) != source_hash:
        raise ValueError('Database file changed during evaluation')
    singles = [x for x in records if x['kind']=='single']
    multi = [x for x in records if x['kind']=='multi']
    negatives = [x for x in records if x['kind']=='negative']
    quarantine = [x for x in records if x['kind']=='quarantine']
    summary = dict(
        single=dict(total=len(singles),raw_recall_at_1=sum(x['raw_codes'][:1]==x['expected_codes'] for x in singles),
            raw_recall_at_3=sum(x['raw_target_hits']==1 for x in singles),
            prepared_recall_at_3=sum(x['prepared_target_hits']==1 for x in singles)),
        multi=dict(total=len(multi),raw_all_targets=sum(x['raw_target_hits']==len(x['expected_codes']) for x in multi),
            prepared_all_targets=sum(x['prepared_target_hits']==len(x['expected_codes']) for x in multi),
            raw_any_target=sum(x['raw_target_hits']>0 for x in multi),
            raw_target_hits=sum(x['raw_target_hits'] for x in multi),target_slots=sum(len(x['expected_codes']) for x in multi)),
        negative=dict(total=len(negatives),raw_empty=sum(not x['raw_codes'] for x in negatives),
            prepared_empty=sum(not x['prepared_codes'] for x in negatives)),
        quarantine=dict(total=len(quarantine),cases_without_forbidden_leak=sum(not x['forbidden_leaks'] for x in quarantine)))
    report = dict(evaluated_at=datetime.now(timezone.utc).isoformat(),frozen_at=frozen['frozen_at'],
        cases_artifact=cases_path.name,cases_sha256=file_sha256(cases_path),database_sha256=source_hash,
        implementation_sha256=frozen['implementation_sha256'],rag_implementation_sha256=frozen['rag_implementation_sha256'],
        evaluation_script_sha256=file_sha256(Path(__file__)),summary=summary,records=records,
        frozen_database_sha256=frozen['database_sha256'],snapshot_manifest_sha256=bound_snapshot,
        limits=frozen['limits'],ranking_changed=False,source_changed=False,external_api_calls=0)
    dump(output,report)
    return dict(artifact=str(output),summary=summary,ranking_changed=False,external_api_calls=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',required=True)
    parser.add_argument('--output',required=True)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--db',default=None)
    group.add_argument('--snapshot',default=None)
    args = parser.parse_args()
    database=Path(args.snapshot)/'grammar_reference.sqlite' if args.snapshot else args.db or DB
    print(json.dumps(evaluate(args.cases,args.output,db=database,snapshot=args.snapshot),ensure_ascii=False))


if __name__=='__main__':
    main()
