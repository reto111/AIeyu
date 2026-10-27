"""Verify the frozen thesis supplement using only bundled JSON and the standard library."""
import argparse,json,hashlib
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text('utf8'))
def local(root,name):
    p=(root/name).resolve()
    if not p.is_relative_to(root.resolve()):raise ValueError('Outside supplement')
    return p
def replay(raw,edits):
    cursor=0;parts=[]
    for e in sorted(edits,key=lambda e:e['start']):
        a=e['start'];b=a+len(e['old'])
        if a<cursor or raw[a:b]!=e['old']:raise ValueError('Edit source mismatch')
        parts.extend([raw[cursor:a],e['new']]);cursor=b
    return ''.join(parts)+raw[cursor:]
def verify(root):
    m=read(root/'manifest.json')
    for name,h in m['files'].items():
        if sha(local(root,name))!=h:raise ValueError('Changed supplement file: '+name)
    facts=read(local(root,m['facts']));sources={k:read(local(root,v['path']))for k,v in facts['sources'].items()}
    for v in facts['sources'].values():
        if sha(local(root,v['path']))!=v['sha256']:raise ValueError('Changed statistics source')
    def get(obj,location):
        for key in location.split('.'):obj=obj[key]
        return obj
    overrides=dict(source_groups=lambda:sources['numbered_coverage']['source_universe']+sources['inline']['statistics']['records'],default_groups=lambda:sources['numbered_language']['statistics']['eligible_original_groups']+sources['inline']['statistics']['eligible_original'],explicit_groups=lambda:sources['numbered_language']['statistics']['reviewed_groups']+sources['numbered_mono']['statistics']['reviewed_groups']+sources['inline']['statistics']['eligible_with_candidates'],packages=lambda:len(sources['catalog']['packages']),evidence_reports=lambda:len(sources['catalog']['evidence_reports']),delivery_files=lambda:len(sources['delivery']['files'])+1,isolated_checks=lambda:len(sources['delivery_verification']['checks']))
    base=Path(facts['sources']['catalog']['path']).parent;payload_files=0
    for item in sources['catalog']['packages']:
        p=local(root,(base/item['manifest']).as_posix())
        if sha(p)!=item['manifest_sha256']:raise ValueError('Changed package manifest')
        payload_files+=len(read(p)['files'])
    overrides['package_payload_files']=lambda:payload_files
    for label,source in [('numbered','numbered_review'),('inline','inline_review')]:overrides[label+'_review_cells']=lambda source=source:sources[source]['item_count']*len(sources[source]['fields'])*2
    for f in facts['facts']:
        value=overrides[f['fact_id']]()if f['fact_id']in overrides else get(sources[f['source']],f['location_or_derivation'])
        if value!=f['value']:raise ValueError('Derived fact mismatch: '+f['fact_id'])
    units=read(root/'source_units.json');originals={(r['code'],r['claim_number']):r for r in read(root/'selected_original_claims.json')};review=read(local(root,m['claim_review']));contexts=0
    for code,u in units.items():
        if hashlib.sha256(u['source_text'].encode('utf8')).hexdigest()!=u['source_unit_sha256']or replay(u['source_text'],u['edits'])!=u['candidate_text']:raise ValueError('Source/candidate unit mismatch')
        if hashlib.sha256(u['candidate_text'].encode('utf8')).hexdigest()!=u['candidate_unit_sha256']:raise ValueError('Candidate unit hash mismatch')
    for r in review['records']:
        original=originals[r['code'],r['claim_number']];u=units[r['code']];raw=u['source_text']
        if u['source_unit_sha256']!=r['source_unit_sha256']or u['candidate_unit_sha256']!=r['candidate_unit_sha256']:raise ValueError('Source unit pin differs from review')
        if raw[r['existing_quote_source_start']:r['existing_quote_source_end']]!=r['existing_quote']or original['quote']!=r['existing_quote']or original['text_zh']!=r['claim_text']:raise ValueError('Original claim or quote mismatch')
        for c in r['supplemental_context']:
            u=units[c['source_code']];a,b=c['source_start'],c['source_end'];raw=u['source_text']
            if u['source_unit_sha256']!=c['source_unit_sha256']or u['candidate_unit_sha256']!=c['candidate_unit_sha256']:raise ValueError('Context unit pin differs from review')
            inside=[];shift=0
            for e in u['edits']:
                x=e['start'];y=x+len(e['old'])
                if y<=a:shift+=len(e['new'])-len(e['old'])
                elif x<b and y>a:
                    if not a<=x<=y<=b:raise ValueError('Context cuts an edit')
                    inside.append({**e,'start':x-a})
            candidate=replay(raw[a:b],inside)
            if raw[a:b]!=c['source_text']or candidate!=c['candidate_text']or u['candidate_text'][a+shift:a+shift+len(candidate)]!=candidate:raise ValueError('Context range mismatch')
            contexts+=1
    if len(originals)!=10 or len(review['records'])!=10 or contexts!=20 or len(facts['facts'])!=42:raise ValueError('Unexpected frozen scope')
    return dict(verified=True,facts=42,source_json_files=len(sources),original_quotes=10,supplemental_context_ranges=contexts,source_units=len(units),package_manifests=len(sources['catalog']['packages']),independent_semantic_review=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);a=p.parse_args();print(json.dumps(verify(a.root),ensure_ascii=False))
