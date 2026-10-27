"""Read a pinned extent collection with explicit candidate scope."""
import argparse,hashlib,json
from pathlib import Path

def read_collection(directory):
    directory=Path(directory).resolve();m=json.loads((directory/'manifest.json').read_text('utf8'))
    for name,pin in m['files'].items():
        p=(directory/name).resolve()
        if not p.is_relative_to(directory)or hashlib.sha256(p.read_bytes()).hexdigest()!=pin:raise ValueError('Extent collection changed')
    rows=[json.loads(s)for s in (directory/'examples.jsonl').read_text('utf8').splitlines()]
    if len(rows)!=m['statistics']['reviewed_anchors']or len({x['example_id']for x in rows})!=len(rows):raise ValueError('Extent count changed')
    return m,rows

def select(rows,include_candidates=False,example_id=None):
    states={'original_source_ready','model_editorial_candidate'}if include_candidates else{'original_source_ready'}
    return [x for x in rows if x['state']in states and (example_id is None or x['example_id']==example_id)]

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['verify','list','show']);p.add_argument('--collection',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--id');p.add_argument('--include-candidates',action='store_true');a=p.parse_args()
    m,rows=read_collection(a.collection)
    if a.command=='verify':print(json.dumps(dict(verified=True,statistics=m['statistics']),ensure_ascii=False))
    else:
        if a.command=='show'and not a.id:p.error('show requires --id')
        chosen=select(rows,a.include_candidates,a.id)
        print(json.dumps(chosen if a.command=='show'else[dict(example_id=x['example_id'],source_unit=x['source_unit'],state=x['state'],pdf_pages=[p['pdf_page']for p in x['page_evidence']])for x in chosen],ensure_ascii=False,indent=2))
