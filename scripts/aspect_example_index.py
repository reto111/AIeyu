"""Read-only, scope-checked access to the numbered textbook anchor index."""
from __future__ import annotations
import argparse,hashlib,json,sqlite3
from pathlib import Path
from contextlib import closing

DEFAULT_DIRECTORY=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference/research_exports/aspect_numbered_examples_20261023_002'
if (Path(__file__).resolve().parent/'manifest.json').exists():DEFAULT_DIRECTORY=Path(__file__).resolve().parent
def fsh(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(directory=DEFAULT_DIRECTORY):
    directory=Path(directory).resolve();manifest=json.loads((directory/'manifest.json').read_text('utf8'))
    inventory={p.relative_to(directory).as_posix()for p in directory.rglob('*')if p.is_file()and p.name!='manifest.json'}
    if inventory!=set(manifest['files']):raise ValueError('Example package inventory mismatch')
    for name,pin in manifest['files'].items():
        p=(directory/name).resolve()
        if not p.is_relative_to(directory)or fsh(p)!=pin:raise ValueError('Example package fingerprint mismatch')
    return manifest

def query(*,directory=DEFAULT_DIRECTORY,contains=None,chapter=None,unit=None,example_id=None,include_candidates=False,limit=20):
    directory=Path(directory).resolve();manifest=verify(directory)
    if not isinstance(limit,int)or not 1<=limit<=100:raise ValueError('Invalid result limit')
    if chapter is not None and(not isinstance(chapter,int)or not 1<=chapter<=14):raise ValueError('Invalid chapter')
    if contains is not None and(not isinstance(contains,str)or not contains or len(contains)>500):raise ValueError('Invalid literal substring')
    clauses=['state in (?,?)'if include_candidates else'state=?']
    params=['original_source_ready','model_editorial_candidate']if include_candidates else['original_source_ready']
    for column,value in [('chapter',chapter),('source_unit',unit),('example_id',example_id)]:
        if value is not None:clauses.append(column+'=?');params.append(value)
    if contains is not None:
        # instr is literal; %, _ and backslashes cannot turn into wildcards.
        clauses.append('instr('+('candidate_text'if include_candidates else'source_text')+',?)>0');params.append(contains)
    with closing(sqlite3.connect((directory/'examples.sqlite').as_uri()+'?mode=ro',uri=True))as c:
        c.row_factory=sqlite3.Row
        rows=c.execute('select metadata_json from examples where '+' and '.join(clauses)+' order by source_unit,book_number,example_id limit ?',params+[limit]).fetchall()
    sources=[]
    for row in rows:
        item=json.loads(row['metadata_json'])
        if not item['eligible_with_candidates']or(not include_candidates and not item['eligible_original']):raise ValueError('Scope metadata mismatch')
        for field in ('source_text','candidate_text'):
            if hashlib.sha256(item[field].encode('utf8')).hexdigest()!=item[field+'_sha256']:raise ValueError('Example text mismatch')
        sources.append(item)
    return dict(status='found'if sources else'no_evidence',edition=manifest['edition'],manifest_sha256=fsh(directory/'manifest.json'),include_candidates=include_candidates,records=sources,record_kind='numbered_example_anchor_paragraph',complete_example_boundary_assessed=False,language_alignment_assessed=False,generation_called=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['verify','search','show']);p.add_argument('--directory',type=Path,default=DEFAULT_DIRECTORY);p.add_argument('--contains');p.add_argument('--chapter',type=int);p.add_argument('--unit');p.add_argument('--id',dest='example_id');p.add_argument('--include-candidates',action='store_true');p.add_argument('--limit',type=int,default=20);p.add_argument('--output',type=Path);a=p.parse_args()
    if a.command=='show'and not a.example_id:p.error('show requires --id')
    result=dict(verified_files=len(verify(a.directory)['files']))if a.command=='verify'else query(directory=a.directory,contains=a.contains,chapter=a.chapter,unit=a.unit,example_id=a.example_id,include_candidates=a.include_candidates,limit=a.limit)
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if a.output:a.output.write_text(text,'utf8')
    else:print(text)
