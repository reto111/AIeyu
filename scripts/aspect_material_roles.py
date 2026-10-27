"""Read-only literal lookup of reviewed textbook paragraph roles."""
import argparse,hashlib,json
from pathlib import Path
from collections import Counter

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read_collection(root):
    root=root.resolve();m=json.loads((root/'manifest.json').read_text('utf8'))
    for rel,h in m['files'].items():
        p=(root/rel).resolve()
        if not p.is_relative_to(root)or sha(p)!=h:raise ValueError('Material package file mismatch')
    rows=list(map(json.loads,(root/'paragraphs.jsonl').read_text('utf8').splitlines()))
    if len(rows)!=m['statistics']['paragraphs']or len({r['residual_id']for r in rows})!=len(rows):raise ValueError('Material package count mismatch')
    return m,rows

def select(rows,include_candidates=False,role=None,unit=None,text=None,residual_id=None):
    states={'original_source_ready','model_editorial_candidate'}if include_candidates else{'original_source_ready'}
    return [r for r in rows if r['state']in states and (role is None or r['paragraph_role']==role)and(unit is None or r['source_unit']==unit)and(residual_id is None or r['residual_id']==residual_id)and(text is None or text.casefold()in r['candidate_text'].casefold()or text.casefold()in r['source_text'].casefold())]

def main():
    p=argparse.ArgumentParser(description='教材段落材料角色：字面检索，不是语义标签或语料库频率。');p.add_argument('command',choices=['verify','stats','list','show','search']);p.add_argument('--collection',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--include-candidates',action='store_true');p.add_argument('--role');p.add_argument('--unit');p.add_argument('--text');p.add_argument('--id');p.add_argument('--offset',type=int,default=0);p.add_argument('--limit',type=int,default=20);a=p.parse_args()
    if a.offset<0 or not 1<=a.limit<=100:p.error('offset must be nonnegative; limit must be 1–100')
    m,rows=read_collection(a.collection)
    if a.command=='verify':out=dict(verified=True,statistics=m['statistics'])
    else:
        if a.command=='show'and not a.id:p.error('show requires --id')
        if a.command=='search'and not a.text:p.error('search requires --text')
        chosen=select(rows,a.include_candidates,a.role,a.unit,a.text,a.id)
        if a.command=='stats':out=dict(paragraphs=len(chosen),roles=dict(Counter(r['paragraph_role']for r in chosen)),states=dict(Counter(r['state']for r in chosen)),semantic_correctness_certified=False)
        elif a.command=='show':out=chosen
        else:out=dict(total=len(chosen),offset=a.offset,records=[{k:r[k]for k in ['residual_id','source_unit','state','paragraph_role','page_evidence','extracted_illustration_ids','table_ids']}for r in chosen[a.offset:a.offset+a.limit]])
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
