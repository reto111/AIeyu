"""Read-only, scope-filtered access to a pinned unnumbered example package."""
import argparse,json,hashlib
from pathlib import Path
def read_collection(root):
    root=root.resolve();m=json.loads((root/'manifest.json').read_text('utf8'))
    for rel,h in m['files'].items():
        p=(root/rel).resolve()
        if not p.is_relative_to(root)or hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise ValueError('Package file mismatch')
    rows=[json.loads(s)for s in(root/'examples.jsonl').read_text('utf8').splitlines()]
    if len(rows)!=m['statistics']['records']or len({r['example_id']for r in rows})!=len(rows):raise ValueError('Invalid package count')
    return m,rows
def select(rows,include_candidates=False,example_id=None):
    states={'original_source_ready','model_editorial_candidate'}if include_candidates else{'original_source_ready'}
    return [r for r in rows if r['state']in states and (example_id is None or r['example_id']==example_id)]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['verify','list','show']);p.add_argument('--collection',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--include-candidates',action='store_true');p.add_argument('--id');a=p.parse_args();m,rows=read_collection(a.collection)
    if a.command=='verify':print(json.dumps(dict(verified=True,statistics=m['statistics']),ensure_ascii=False))
    else:
        if a.command=='show'and not a.id:p.error('show requires --id')
        chosen=select(rows,a.include_candidates,a.id);print(json.dumps(chosen if a.command=='show'else[dict(example_id=r['example_id'],source_unit=r['source_unit'],state=r['state'])for r in chosen],ensure_ascii=False,indent=2))
