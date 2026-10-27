"""Rebuild exact corpus ranges and check inherited query scope."""
import argparse,csv,json
from pathlib import Path
from datetime import datetime,timezone
from build_aspect_example_index import fsh,read,write
from build_aspect_corpus_extents import materialize_corpus,materialize_exclusions
from aspect_corpus_extents import read_collection,select

def verify(collection,candidate,index,pilot_extents,previous=()):
    collection=Path(collection);m,rows=read_collection(collection);reviews=[collection/name for name in m['review_file_pins']]
    rebuilt,pins,review_pins=materialize_corpus(candidate,index,pilot_extents,reviews)
    if rows!=rebuilt or pins!=m['source_pins']or review_pins!=m['review_file_pins']:raise ValueError('Corpus replay mismatch')
    excluded=materialize_exclusions(candidate,index,reviews,rows);saved=[json.loads(s)for s in(collection/'excluded_anchors.jsonl').read_text('utf8').splitlines()]
    if excluded!=saved:raise ValueError('Exclusions replay mismatch')
    with(collection/'examples.tsv').open(encoding='utf-8-sig',newline='')as f:tab=list(csv.DictReader(f,delimiter='\t'))
    if len(tab)!=len(rows):raise ValueError('TSV count mismatch')
    for x,y in zip(rows,tab):
        if any(str(x[k])!=y[k]for k in y):raise ValueError('TSV field mismatch')
        if bool(select(rows,False,x['example_id']))!=(x['state']=='original_source_ready')or bool(select(rows,True,x['example_id']))!=(x['state']!='withheld'):raise ValueError('Query scope mismatch')
    if any(select(rows,True,x['example_id'])for x in excluded):raise ValueError('Excluded author exposition returned')
    byid={x['example_id']:x for x in rows};prior=[]
    for directory in map(Path,previous):
        pm,old=read_collection(directory)
        if not all(byid.get(x['example_id'])==x for x in old):raise ValueError('Previous records changed')
        prior.append(dict(edition=directory.name,manifest_sha256=fsh(directory/'manifest.json'),records=len(old),identical=True))
    original=Path(candidate).resolve().parent.parent/'aspect_reference.sqlite';expected_original=read(Path(candidate)/'manifest.json')['source_db_sha256']
    if fsh(original)!=expected_original:raise ValueError('Original source database changed')
    return dict(created_at=datetime.now(timezone.utc).isoformat(),edition=collection.name,manifest_sha256=fsh(collection/'manifest.json'),records_rebuilt=len(rows),tsv_records_rebuilt=len(tab),exclusions_rebuilt=len(excluded),scope_checks=2*len(rows),default_returned=len(select(rows)),explicit_candidate_returned=len(select(rows,True)),withheld_never_returned=sum(x['state']=='withheld'for x in rows),excluded_never_returned=True,prior_versions=prior,source_pins=pins,original_source_db_sha256=expected_original,statistics=m['statistics'],independent_boundary_review=False,semantic_accuracy_assessed=False)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['collection','candidate','index','pilot-extents','report']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--previous',type=Path,action='append',default=[]);a=p.parse_args()
    if a.report.exists():raise FileExistsError('Choose an unused verification report')
    result=verify(a.collection,a.candidate,a.index,a.pilot_extents,a.previous);write(a.report,result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
