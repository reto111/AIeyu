"""Read numbered language annotations joined to the existing group index by stable ID."""
import argparse,json
from pathlib import Path
from collections import Counter
import sys
sys.dont_write_bytecode=True
from aspect_corpus_search import load as load_groups,select,search,citation_records,sha,local
EXTRA_KEYS={'numbered_parallel_language':'bilingual','numbered_monolingual_language':'monolingual'}
HERE=Path(__file__).resolve().parent
DEFAULT=HERE/'research_catalog_20261026_004.json'
if not DEFAULT.exists():DEFAULT=HERE.parent/'data/processed/aspect_reference/research_catalog_20261026_004.json'

def load(catalog):
    catalog=catalog.resolve();rows,pins=load_groups(catalog);byid={r['example_id']:r for r in rows};data=json.loads(catalog.read_text('utf8'));annotations={};extra={};pending={}
    candidate_versions=set()
    for item in data['packages']:
        if item['key']not in EXTRA_KEYS:continue
        if item['key']in extra:raise ValueError('Duplicate language collection')
        p=local(catalog.parent,item['manifest'])
        if sha(p)!=item['manifest_sha256']:raise ValueError('Language manifest version mismatch')
        m=json.loads(p.read_text('utf8'))
        for rel,h in m['files'].items():
            if sha(local(p.parent,rel))!=h:raise ValueError('Changed language payload')
        groups=list(map(json.loads,(p.parent/'groups.jsonl').read_text('utf8').splitlines()))
        if len(groups)!=m['statistics']['reviewed_groups']:raise ValueError('Language group count mismatch')
        if sum(len(r['pairs'])for r in groups)!=m['statistics']['component_correspondences']:raise ValueError('Correspondence count mismatch')
        srcpins=m['source_pins'];candidate_versions.add(srcpins['candidate_manifest_sha256'])
        if srcpins['numbered_manifest_sha256']!=pins['numbered_complete_extents']['sha256']:raise ValueError('Incompatible numbered source')
        for r in groups:
            key=r['example_id'];source=byid.get(key)
            if key in annotations or source is None:raise ValueError('Duplicate or unknown annotated ID')
            if source['collection_kind']!='numbered_group'or source['state']=='withheld':raise ValueError('Invalid annotated source scope')
            for field in ['source_unit','state','source_text','candidate_text','source_start','source_end','page_evidence']:
                if r[field]!=source[field]:raise ValueError('Annotation source mismatch: '+field)
            kind=EXTRA_KEYS[item['key']]
            if(kind=='bilingual')!=bool(r['pairs']):raise ValueError('Language kind mismatch')
            if kind=='monolingual'and(len(r['language_components'])!=1 or r['language']not in ['ru','zh']):raise ValueError('Invalid monolingual components')
            annotations[key]=dict(language_layer=kind,**r)
        extra[item['key']]=dict(manifest=item['manifest'],sha256=sha(p),source_pins=srcpins)
        file='unreviewed_example_ids.json'if item['key']=='numbered_parallel_language'else'unreviewed_after_both_layers.json'
        pending[item['key']]=set(json.loads((p.parent/file).read_text('utf8')))
    if set(extra)!=set(EXTRA_KEYS)or len(candidate_versions)!=1:raise ValueError('Missing or incompatible language collections')
    basepath=local(catalog.parent,pins['numbered_complete_extents']['manifest']);base=json.loads(basepath.read_text('utf8'));version=base.get('candidate_manifest_sha256',base.get('source_pins',{}).get('candidate_manifest_sha256'))
    if candidate_versions!={version}:raise ValueError('Incompatible candidate source')
    if extra['numbered_monolingual_language']['source_pins']['parallel_manifest_sha256']!=extra['numbered_parallel_language']['sha256']:raise ValueError('Monolingual predecessor mismatch')
    numbered={r['example_id']for r in rows if r['collection_kind']=='numbered_group'};paired={key for key,r in annotations.items()if r['language_layer']=='bilingual'};remaining=numbered-set(annotations)
    if pending['numbered_parallel_language']!=numbered-paired or pending['numbered_monolingual_language']!=remaining:raise ValueError('Language coverage mismatch')
    if any(byid[key]['state']!='withheld'for key in remaining):raise ValueError('Unreviewed eligible numbered source')
    return rows,{**pins,**extra},annotations

def show(rows,annotations,ids,layer='candidate_text'):
    out=citation_records(rows,ids,layer)
    for r in out:
        a=annotations.get(r['example_id'])
        if a:
            r['language_annotation']=a
            r['language_scope_warning_zh']='教材例证组成部分范围；可能包含已另标的比较词形或语境。原转录/编校候选分层；不是逐句翻译金标、自然语料或独立专家评价。'
        else:r['language_annotation']=None
    return out

def main():
    p=argparse.ArgumentParser(description='编号语言范围按ID挂接；组数不重复计算。');p.add_argument('command',choices=['stats','search','show']);p.add_argument('--catalog',type=Path,default=DEFAULT);p.add_argument('--include-candidates',action='store_true');p.add_argument('--id',action='append');p.add_argument('--term',action='append');p.add_argument('--layer',choices=['source_text','candidate_text'],default='candidate_text');p.add_argument('--match',choices=['substring','cyrillic_form'],default='substring');p.add_argument('--offset',type=int,default=0);p.add_argument('--limit',type=int,default=10);a=p.parse_args()
    if a.offset<0 or not 1<=a.limit<=100:p.error('offset must be nonnegative; limit must be 1–100')
    rows,pins,annotations=load(a.catalog);chosen=select(rows,a.include_candidates);eligible={r['example_id']for r in chosen};joined=[r for key,r in annotations.items()if key in eligible]
    result=dict(catalog_sha256=sha(a.catalog),verified_collections=pins,scope_include_candidates=a.include_candidates,eligible_groups=len(chosen),eligible_by_kind=dict(Counter(r['collection_kind']for r in chosen)),numbered_language_annotated_groups=len(joined),numbered_language_by_kind=dict(Counter(r['language_layer']for r in joined)),numbered_component_correspondences=sum(len(r['pairs'])for r in joined),counts_are_distinct_group_ids=True,natural_corpus_frequency_assessed=False)
    if a.command=='show':
        if not a.id:p.error('show requires --id')
        found=show(chosen,annotations,a.id,a.layer);result.update(matching_groups=len(found),records=found[a.offset:a.offset+a.limit])
    if a.command=='search':
        if not a.term:p.error('search requires --term')
        try:found=search(chosen,a.term,a.layer,a.match)
        except ValueError as error:p.error(str(error))
        for r in found:
            annotation=annotations.get(r['example_id']);r['numbered_language_layer']=annotation['language_layer']if annotation else None
        result.update(query_terms=a.term,matching_groups=len(found),records=found[a.offset:a.offset+a.limit],text_scope='whole_group_including_labels_attribution_translation_and_comparison',matching_positions_are_group_local_not_pdf_coordinates=True)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
