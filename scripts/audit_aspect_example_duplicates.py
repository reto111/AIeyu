"""Describe repeated textbook text without merging source occurrences or contexts."""
import argparse,json,hashlib,re
from pathlib import Path
from collections import defaultdict
from aspect_corpus_search import load,select,local,sha

def normalized(text,mode):
    if mode=='exact':return text
    if mode=='whitespace':return re.sub(r'\s+',' ',text).strip()
    raise ValueError('Unsupported normalization')

def clusters(rows,layer,mode):
    groups=defaultdict(list)
    for r in rows:groups[normalized(r[layer],mode)].append(r)
    repeated=[]
    for text,rs in groups.items():
        if len(rs)<2:continue
        repeated.append(dict(text_sha256=hashlib.sha256(text.encode('utf8')).hexdigest(),comparison_text=text,occurrences=[dict(example_id=r['example_id'],source_unit=r['source_unit'],state=r['state'],collection_kind=r['collection_kind'],pdf_pages=sorted({p['pdf_page']for p in r['page_evidence']}))for r in sorted(rs,key=lambda r:r['example_id'])]))
    repeated.sort(key=lambda r:(-len(r['occurrences']),r['text_sha256']))
    return dict(input_groups=len(rows),distinct_text_keys=len(groups),repeated_text_keys=len(repeated),occurrences_in_repeated_keys=sum(len(r['occurrences'])for r in repeated),excess_occurrences_over_one_per_text=sum(len(r['occurrences'])-1 for r in repeated),cross_collection_repeated_keys=sum(len({o['collection_kind']for o in r['occurrences']})>1 for r in repeated),groups=repeated)

def contained_fragments(rows,layer):
    ordered=sorted(((r[layer],r)for r in rows),key=lambda x:(len(x[0]),x[1]['example_id']));matches=[]
    for i,(short,a)in enumerate(ordered):
        if len(re.sub(r'\s','',short))<20:continue
        for long,b in ordered[i+1:]:
            if len(long)<=len(short):continue
            start=long.find(short)
            if start<0:continue
            matches.append(dict(shorter_example_id=a['example_id'],longer_example_id=b['example_id'],shorter_text=short,longer_layer_local_start=start,longer_layer_local_end=start+len(short),same_source_unit=a['source_unit']==b['source_unit'],shorter_kind=a['collection_kind'],longer_kind=b['collection_kind']))
    return dict(minimum_shorter_nonwhitespace_characters=20,matching_pairs=len(matches),shorter_group_ids=len({r['shorter_example_id']for r in matches}),longer_group_ids=len({r['longer_example_id']for r in matches}),pairs=matches,meaning_zh='较短组的完整文本逐字包含于较长组；不是句法切分或语义等价，也不证明同一出处。只报首个出现位置。')

def audit(catalog):
    rows,pins=load(catalog);d=json.loads(catalog.read_text('utf8'));base=catalog.resolve().parent
    scopes={'original_ready':select(rows),'including_model_candidates':select(rows,True)}
    reports={scope:{layer:{mode:clusters(chosen,layer,mode)for mode in ['exact','whitespace']}for layer in ['source_text','candidate_text']}for scope,chosen in scopes.items()}
    changes=[]
    for scope,chosen in scopes.items():
        for mode in ['exact','whitespace']:
            by_candidate=defaultdict(list)
            for r in chosen:by_candidate[normalized(r['candidate_text'],mode)].append(r)
            for text,rs in by_candidate.items():
                source_keys={normalized(r['source_text'],mode)for r in rs}
                if len(source_keys)>1:changes.append(dict(scope=scope,normalization=mode,candidate_text_sha256=hashlib.sha256(text.encode('utf8')).hexdigest(),example_ids=sorted(r['example_id']for r in rs),distinct_source_keys=len(source_keys)))
    pair_item=next(x for x in d['packages']if x['key']=='unnumbered_parallel_supplement');p=local(base,pair_item['manifest']);assert sha(p)==pair_item['manifest_sha256'];m=json.loads(p.read_text('utf8'))
    for rel,h in m['files'].items():
        if sha(local(p.parent,rel))!=h:raise ValueError('Changed pair payload')
    pairs=list(map(json.loads,(p.parent/'pairs.jsonl').read_text('utf8').splitlines()));assert len(pairs)==m['statistics']['pairs']
    pair_reports={}
    for mode in ['exact','whitespace']:
        groups=defaultdict(list)
        for pair in pairs:groups[tuple(normalized(pair[lang]['candidate_text'],mode)for lang in ['ru','zh'])].append(pair)
        repeats=[dict(ru=key[0],zh=key[1],pair_ids=sorted(r['pair_id']for r in rs),example_ids=sorted(r['example_id']for r in rs))for key,rs in groups.items()if len(rs)>1]
        pair_reports[mode]=dict(input_pairs=len(pairs),distinct_pair_text_keys=len(groups),repeated_pair_text_keys=len(repeats),excess_occurrences_over_one_per_text=sum(len(r['pair_ids'])-1 for r in repeats),groups=sorted(repeats,key=lambda r:r['pair_ids']))
    containment={scope:{layer:contained_fragments(chosen,layer)for layer in ['source_text','candidate_text']}for scope,chosen in scopes.items()}
    return dict(schema_version=2,script_sha256=sha(Path(__file__)),catalog_sha256=sha(catalog),collection_pins=pins,pair_manifest_sha256=sha(p),normalization_definitions=dict(exact='字符完全相同；不改大小写、标点、重音或ё。',whitespace='仅Python正则\\s+折叠为一个空格并去首尾空白；其他字符不动。'),scope_reports=reports,exact_containment_reports=containment,candidate_text_collisions_from_distinct_source_keys=changes,pair_reports=pair_reports,source_records_merged=0,natural_corpus_sentences_counted=False,semantic_equivalence_assessed=False,interpretation_zh='不同位置重引、作者改写及相同短句可能有不同语境；相同文本键不能证明来源相同或语用功能相同。本报告只展示重复，不删除、合并或改写记录。去重前需决定论文抽样单位；教材组数量不能当自然句频率。')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError('Immutable duplicate audit')
    result=audit(a.catalog);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({scope:{layer:{mode:{k:v for k,v in row.items()if k!='groups'}for mode,row in modes.items()}for layer,modes in layers.items()}for scope,layers in result['scope_reports'].items()},ensure_ascii=False))
