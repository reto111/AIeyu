"""Literal lookup over complete numbered and reviewed inline textbook groups."""
import argparse,json,hashlib,re
from pathlib import Path
from collections import Counter
DEFAULT=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference/research_catalog_20261024_014.json'
KEYS={'numbered_complete_extents':'numbered_group','unnumbered_supplement':'inline_supplement_group'}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local(root,relative):
    p=(root/relative).resolve()
    if not p.is_relative_to(root.resolve()):raise ValueError('Collection path escapes root')
    return p

def load(catalog):
    catalog=catalog.resolve();d=json.loads(catalog.read_text('utf8'));rows=[];pins={};versions=set();seen=set()
    for item in d['packages']:
        if item['key']not in KEYS:continue
        if item['key']in pins:raise ValueError('Duplicate catalog collection')
        p=local(catalog.parent,item['manifest'])
        if sha(p)!=item['manifest_sha256']:raise ValueError('Manifest version mismatch')
        m=json.loads(p.read_text('utf8'))
        for rel,h in m['files'].items():
            if sha(local(p.parent,rel))!=h:raise ValueError('Changed collection payload')
        version=m.get('candidate_manifest_sha256',m.get('source_pins',{}).get('candidate_manifest_sha256'))
        if not version:raise ValueError('Missing common candidate version')
        versions.add(version);group=list(map(json.loads,(p.parent/'examples.jsonl').read_text('utf8').splitlines()))
        expected=m['statistics'].get('records',m['statistics'].get('reviewed_anchors'))
        if len(group)!=expected:raise ValueError('Collection count mismatch')
        for r in group:
            if r['example_id']in seen:raise ValueError('Duplicate cross-collection ID')
            seen.add(r['example_id']);rows.append(dict(collection_kind=KEYS[item['key']],**r))
        pins[item['key']]=dict(manifest=item['manifest'],sha256=sha(p))
    if set(pins)!=set(KEYS)or len(versions)!=1:raise ValueError('Missing or incompatible source collections')
    return rows,pins

def select(rows,include_candidates=False,kind=None):
    states={'original_source_ready','model_editorial_candidate'}if include_candidates else{'original_source_ready'}
    return [r for r in rows if r['state']in states and(kind is None or r['collection_kind']==kind)]

def search(rows,terms,layer='candidate_text',match_mode='substring'):
    if layer not in ['source_text','candidate_text']or not terms or any(not t.strip()for t in terms):raise ValueError('Nonempty literal terms and a valid text layer are required')
    if match_mode not in ['substring','cyrillic_form']:raise ValueError('Unknown literal match mode')
    terms=list(dict.fromkeys(terms))
    if match_mode=='cyrillic_form'and any(not re.fullmatch('[А-Яа-яЁё]+',t)for t in terms):raise ValueError('Cyrillic form mode requires individual Russian letter forms')
    patterns=[re.compile(('(?<![А-Яа-яЁё])'+re.escape(t)+'(?![А-Яа-яЁё])')if match_mode=='cyrillic_form'else re.escape(t),re.IGNORECASE)for t in terms];found=[]
    for r in rows:
        if r['state']not in {'original_source_ready','model_editorial_candidate'}:continue
        text=r[layer];matches=[p.search(text)for p in patterns]
        if not all(matches):continue
        found.append(dict(example_id=r['example_id'],source_unit=r['source_unit'],state=r['state'],collection_kind=r['collection_kind'],text_layer=layer,example_page_evidence=r['page_evidence'],literal_matches=[dict(term=t,layer_local_start=m.start(),layer_local_end=m.end(),matched_text=m.group(),excerpt=text[max(0,m.start()-50):min(len(text),m.end()+100)])for t,m in zip(terms,matches)]))
    return sorted(found,key=lambda r:(r['collection_kind'],r['example_id']))

def citation_records(rows,ids,layer='candidate_text'):
    if layer not in ['source_text','candidate_text']or not ids or any(not key.strip()for key in ids):raise ValueError('Nonempty IDs and valid text layer required')
    wanted=set(ids);result=[]
    for r in rows:
        if r['example_id']not in wanted or r['state']not in {'original_source_ready','model_editorial_candidate'}:continue
        result.append(dict(example_id=r['example_id'],source_unit=r['source_unit'],state=r['state'],collection_kind=r['collection_kind'],text_layer=layer,selected_text=r[layer],source_transcription=r['source_text'],editorial_candidate=r['candidate_text'],editorial_difference=r['source_text']!=r['candidate_text'],page_evidence=r['page_evidence'],source_start=r['source_start'],source_end=r['source_end'],source_offsets_layer='archived_source_transcription',citation_kind='textbook_illustration_group',independent_review=False,warning_zh='原转录与编校候选均经排版线性化；引用须标明文本层、来源页及版本，不能冒称自然语料或专家认证原文。整组可能包含署名、汉译、星号、比较和作者插语。'))
    return sorted(result,key=lambda r:r['example_id'])

def main():
    p=argparse.ArgumentParser(description='教材例组字面AND检索，不作词形还原、频率或自然语料推断。');p.add_argument('command',choices=['stats','search','show']);p.add_argument('--id',action='append');p.add_argument('--catalog',type=Path,default=DEFAULT);p.add_argument('--term',action='append');p.add_argument('--match',choices=['substring','cyrillic_form'],default='substring');p.add_argument('--layer',choices=['source_text','candidate_text'],default='candidate_text');p.add_argument('--kind',choices=list(KEYS.values()));p.add_argument('--include-candidates',action='store_true');p.add_argument('--offset',type=int,default=0);p.add_argument('--limit',type=int,default=10);a=p.parse_args()
    if a.offset<0 or not 1<=a.limit<=100:p.error('offset must be nonnegative; limit must be 1–100')
    rows,pins=load(a.catalog);chosen=select(rows,a.include_candidates,a.kind);result=dict(catalog_sha256=sha(a.catalog),verified_collections=pins,scope_include_candidates=a.include_candidates,eligible_groups=len(chosen),eligible_by_kind=dict(Counter(r['collection_kind']for r in chosen)),eligible_by_state=dict(Counter(r['state']for r in chosen)),natural_corpus_frequency_assessed=False)
    if a.command=='search':
        if not a.term:p.error('search requires --term')
        try:found=search(chosen,a.term,a.layer,a.match)
        except ValueError as error:p.error(str(error))
        result.update(query_terms=a.term,logic='literal_case_insensitive_AND',match_mode=a.match,text_layer=a.layer,matching_groups=len(found),offset=a.offset,records=found[a.offset:a.offset+a.limit],positions_zh='匹配位置仅为所选例文本层内偏移，不是原PDF字形坐标；页证据为整例组范围。')
    elif a.command=='show':
        if not a.id:p.error('show requires --id')
        try:found=citation_records(chosen,a.id,a.layer)
        except ValueError as error:p.error(str(error))
        result.update(requested_ids=list(dict.fromkeys(a.id)),matching_groups=len(found),offset=a.offset,records=found[a.offset:a.offset+a.limit],citation_reference_zh='张家骅：《现代俄语体学（修订本）》，高等教育出版社，2004年第2版。原页与版本清单须随引文保留。')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
