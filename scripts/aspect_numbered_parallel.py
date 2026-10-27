"""Standard-library read-only access to a numbered correspondence package."""
import argparse,hashlib,json
from pathlib import Path
def read_collection(root):
    root=root.resolve();m=json.loads((root/'manifest.json').read_text('utf8'))
    for rel,h in m['files'].items():
        p=(root/rel).resolve()
        if not p.is_relative_to(root)or hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise ValueError('Changed or unsafe payload')
    rows=list(map(json.loads,(root/'groups.jsonl').read_text('utf8').splitlines()))
    if len(rows)!=m['statistics']['reviewed_groups']or len({r['example_id']for r in rows})!=len(rows):raise ValueError('Group count mismatch')
    return m,rows
def select(rows,include_candidates=False):return [r for r in rows if r['state']=='original_source_ready'or(include_candidates and r['state']=='model_editorial_candidate')]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['stats','list','show']);p.add_argument('--collection',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--include-candidates',action='store_true');p.add_argument('--id');a=p.parse_args();m,rows=read_collection(a.collection);rows=select(rows,a.include_candidates)
    if a.command=='show'and not a.id:p.error('show requires --id')
    value=dict(groups=len(rows),component_correspondences=sum(len(r['pairs'])for r in rows),statistics=m['statistics'])if a.command=='stats'else [r for r in rows if a.command!='show'or r['example_id']==a.id]
    print(json.dumps(value,ensure_ascii=False,indent=2))
