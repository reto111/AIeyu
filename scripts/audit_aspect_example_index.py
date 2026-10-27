"""Audit every indexed span against a pinned candidate's original page fragments."""
from pathlib import Path
from collections import Counter
from contextlib import closing
import argparse,datetime,json
import aspect_example_index as api
import build_aspect_example_index as builder

def audit(directory,candidate,output):
    directory=Path(directory).resolve();candidate=Path(candidate).resolve();output=Path(output)
    if output.exists():raise FileExistsError('Immutable audit report')
    manifest=api.verify(directory);cm=builder.verify_candidate(candidate)
    if manifest['source_candidate_manifest_sha256']!=api.fsh(candidate/'manifest.json'):raise ValueError('Foreign candidate')
    rows=[json.loads(x)for x in(directory/'examples.jsonl').read_text('utf8').splitlines()]
    units=[json.loads(x)for x in(directory/'source_units.jsonl').read_text('utf8').splitlines()]
    ids=set();verified=0;context_verified=0;scope_queries=0;counts=Counter();unitcounts=Counter()
    with closing(builder.connect(candidate/'aspect_reference.sqlite'))as src,closing(builder.connect(directory/'examples.sqlite'))as dst:
        if dst.execute('pragma integrity_check').fetchone()[0]!='ok'or dst.execute('pragma foreign_key_check').fetchall():raise ValueError('SQLite integrity failure')
        raw_units={r['code']:dict(r)for r in src.execute('select * from chunks')}
        candidate_units={r['code']:dict(r)for r in src.execute('select * from aspect_candidate_sections')}
        page_spans={u['code']:builder.bindings(src,raw_units[u['code']])for u in units}
        if len(rows)!=dst.execute('select count(*) from examples').fetchone()[0]:raise ValueError('SQLite/JSONL count mismatch')
        for row in rows:
            identity=row['example_id'];code=row['source_unit'];raw=raw_units[code]['body'];meta=json.loads(candidate_units[code]['metadata_json'])
            if identity in ids:raise ValueError('Duplicate anchor id')
            ids.add(identity);unitcounts[code]+=1;counts[row['state']]+=1
            dbrow=dst.execute('select * from examples where example_id=?',(identity,)).fetchone()
            if json.loads(dbrow['metadata_json'])!=row:raise ValueError('SQLite/JSONL record mismatch')
            for key in ('example_id','source_unit','chapter','book_number','state','source_text','candidate_text'):
                if dbrow[key]!=row[key]:raise ValueError('SQLite column/metadata mismatch')
            if row['state']!=candidate_units[code]['state']:raise ValueError('Incorrect anchor state')
            if row['source_unit_sha256']!=builder.tsh(raw)or row['candidate_unit_sha256']!=builder.tsh(candidate_units[code]['body']):raise ValueError('Unit pin mismatch')
            start,end=row['source_start'],row['source_end'];text=raw[start:end]
            if text!=row['source_text']or builder.tsh(text)!=row['source_text_sha256']:raise ValueError('Source anchor mismatch')
            match=builder.ANCHOR.match(text)
            if not match or int(match.group(1))!=row['book_number']or '\n\n'in text:raise ValueError('Incorrect anchor paragraph boundary')
            edited,edits=builder.replay_span(raw,start,end,meta['edits'])
            if edited!=row['candidate_text']or edits!=row['edits']or builder.tsh(edited)!=row['candidate_text_sha256']:raise ValueError('Candidate anchor replay failed')
            if builder.pages_for(page_spans[code],start,end)!=row['page_evidence']:raise ValueError('Anchor page binding failed')
            lo,hi=row['context_source_start'],row['context_source_end'];context,edits=builder.replay_span(raw,lo,hi,meta['edits'])
            if raw[lo:hi]!=row['source_context']or context!=row['candidate_context']or edits!=row['context_edits']:raise ValueError('Context replay failed')
            if builder.pages_for(page_spans[code],lo,hi)!=row['context_page_evidence']:raise ValueError('Context page binding failed')
            if any(row[k]for k in ('complete_example_boundary_assessed','language_alignment_assessed','semantic_labels_assessed')):raise ValueError('Unperformed semantic work claimed')
            verified+=1;context_verified+=1
        for unit in units:
            code=unit['code'];state=unit['state'];expected=[r['example_id']for r in rows if r['source_unit']==code]
            if unitcounts[code]!=unit['anchor_paragraphs']:raise ValueError('Unit count mismatch')
            if len(expected)>100:raise ValueError('Audit needs pagination for unit over query cap')
            for flag in (False,True):
                actual=api.query(directory=directory,unit=code,include_candidates=flag,limit=100)['records'];scope_queries+=1
                allowed=state=='original_source_ready'or(flag and state=='model_editorial_candidate')
                if {x['example_id']for x in actual}!=(set(expected)if allowed else set()):raise ValueError('Query scope failure')
        if len(units)!=100 or dst.execute('select count(*) from source_units').fetchone()[0]!=100:raise ValueError('Unit provenance incomplete')
        for row in dst.execute('select * from source_units'):
            unit=next(x for x in units if x['code']==row['code'])
            if json.loads(row['metadata_json'])!=unit or row['state']!=unit['state']:raise ValueError('Unit SQL/JSONL mismatch')
    if dict(counts)!=manifest['statistics']['counts']or verified!=manifest['statistics']['anchor_paragraphs']:raise ValueError('Manifest count mismatch')
    result=dict(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),manifest_sha256=api.fsh(directory/'manifest.json'),candidate_manifest_sha256=api.fsh(candidate/'manifest.json'),verified_files=len(manifest['files']),anchor_paragraphs_verified=verified,contexts_replayed=context_verified,page_bindings_verified=verified,unit_scope_queries=scope_queries,source_units_verified=len(units),counts=dict(counts),sqlite_integrity='ok',foreign_key_issues=0,complete_example_boundary_assessed=False,language_alignment_assessed=False,limitations='全量验证是精确片段/重放/原页绑定/隔离约束；不是逐例语义、俄汉对齐、全书例句完备性或自然语料频率证明。')
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(audit(a.directory,a.candidate,a.output),ensure_ascii=False,indent=2))
