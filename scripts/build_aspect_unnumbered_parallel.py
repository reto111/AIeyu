"""Export explicitly bounded illustration-level RU/ZH correspondences."""
import argparse,json,csv
from pathlib import Path
from contextlib import closing
from build_aspect_example_index import connect,replay_span,bindings,pages_for,fsh,tsh,write,verify_candidate
from aspect_unnumbered_examples import read_collection
WORK=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference'

def replay_language_span(raw,lo,hi,edits):
    effective=[];projections=[]
    for edit in edits:
        start=edit['start'];old=edit['old'];new=edit['new'];end=start+len(old)
        if not(start<hi and end>lo):continue
        if raw[start:end]!=old:raise ValueError('Stale full editorial edit')
        if lo<=start<end<=hi:effective.append(edit);continue
        prefix=0
        while prefix<min(len(old),len(new))and old[prefix]==new[prefix]:prefix+=1
        suffix=0
        while suffix<min(len(old)-prefix,len(new)-prefix)and old[len(old)-1-suffix]==new[len(new)-1-suffix]:suffix+=1
        a=start+prefix;b=end-suffix;old_part=old[prefix:len(old)-suffix if suffix else len(old)];new_part=new[prefix:len(new)-suffix if suffix else len(new)]
        if a==b:raise ValueError('Cross-boundary insertion needs explicit alignment review')
        if a<hi and b>lo:
            if not lo<=a<b<=hi:raise ValueError('Changed text crosses language boundary')
            projected={**edit,'start':a,'old':old_part,'new':new_part};effective.append(projected)
        projections.append(dict(source_edit=edit,unchanged_prefix_characters=prefix,unchanged_suffix_characters=suffix,changed_source_start=a,changed_source_end=b,changed_text_inside_language_span=lo<=a<b<=hi,projection_kind='trim_exactly_unchanged_outer_text'))
    text,selected=replay_span(raw,lo,hi,effective)
    return text,selected,projections

def materialize(candidate,examples,review):
    verify_candidate(candidate)
    _,source=read_collection(examples);lookup={r['example_id']:r for r in source}
    if review['unnumbered_manifest_sha256']!=fsh(examples/'manifest.json')or review['candidate_manifest_sha256']!=fsh(candidate/'manifest.json'):raise ValueError('Version mismatch')
    pairs=[];seen=set()
    with closing(connect(candidate/'aspect_reference.sqlite'))as c:
        for d in review['pairs']:
            if d['pair_id']in seen:raise ValueError('Duplicate pair ID')
            seen.add(d['pair_id']);r=lookup[d['example_id']]
            unit=c.execute('select * from chunks where code=?',(r['source_unit'],)).fetchone();section=c.execute('select * from aspect_candidate_sections where code=?',(r['source_unit'],)).fetchone();edits=json.loads(section['metadata_json'])['edits'];raw=unit['body'];parts={};ranges=[]
            for language in ['ru','zh']:
                s=d[language];lo=s['source_start'];hi=s['source_end']
                if not r['source_start']<=lo<hi<=r['source_end']:raise ValueError('Language span outside example')
                if tsh(raw[lo:hi])!=s['source_text_sha256']:raise ValueError('Stale language span')
                edited,selected,projections=replay_language_span(raw,lo,hi,edits);parts[language]=dict(source_start=lo,source_end=hi,source_text=raw[lo:hi],candidate_text=edited,edits=selected,page_evidence=pages_for(bindings(c,unit),lo,hi))
                if projections:parts[language]['source_edit_projection']=projections
                ranges.append((lo,hi))
            if ranges[0][0]<ranges[1][1]and ranges[1][0]<ranges[0][1]:raise ValueError('Overlapping languages')
            for previous in pairs:
                if previous['example_id']==d['example_id']:
                    for old in [previous['ru'],previous['zh']]:
                        if any(lo<old['source_end']and hi>old['source_start']for lo,hi in ranges):raise ValueError('Overlapping pair spans')
            pages={p['pdf_page']for v in parts.values()for p in v['page_evidence']}
            if pages!=set(d['visually_checked_pdf_pages']):raise ValueError('Incomplete page review')
            pairs.append(dict(pair_id=d['pair_id'],example_id=d['example_id'],source_unit=r['source_unit'],state=r['state'],**parts,
                review_note_zh=d['review_note_zh'],alignment_level='whole_illustration',translation_gold=False,sentence_alignment_assessed=False,semantic_labels_assessed=False,independent_review=False))
    covered={p['example_id']for p in pairs};ruonly=review['russian_only_examples']
    if len(ruonly)!=len(set(ruonly))or set(ruonly)&covered or set(ruonly)|covered!=set(lookup):raise ValueError('Incomplete example accounting')
    for key in ruonly:
        if any('\u3400'<=ch<='\u9fff'for ch in lookup[key]['source_text']):raise ValueError('Chinese text wrongly marked Russian only')
    return pairs

def build(candidate,examples,review_path,output):
    if output.exists():raise FileExistsError('Immutable parallel supplement')
    review=json.loads(review_path.read_text('utf8'));pairs=materialize(candidate,examples,review);output.mkdir(parents=True)
    (output/'pairs.jsonl').write_text(''.join(json.dumps(p,ensure_ascii=False)+'\n'for p in pairs),'utf8')
    write(output/'russian_only_examples.json',review['russian_only_examples'])
    with(output/'pairs.tsv').open('w',encoding='utf8',newline='')as stream:
        w=csv.writer(stream,delimiter='\t');w.writerow(['pair_id','example_id','state','source_ru','source_zh','candidate_ru','candidate_zh'])
        for p in pairs:w.writerow([p['pair_id'],p['example_id'],p['state'],p['ru']['source_text'],p['zh']['source_text'],p['ru']['candidate_text'],p['zh']['candidate_text']])
    (output/'README.md').write_text(f'''# 无编号例证的俄汉整例对应补充

本版{len(pairs)}个俄汉整例对应，覆盖{len({p['example_id']for p in pairs})}个例组；另{len(review['russian_only_examples'])}组圈定片段仅收俄文，不补译。部分对应汉语位于作者分析中，未据此跨越论述拼接新译对；不能把本层未收汉译说成原书从无汉译。比较组可有多个对应，作者改写式留在原例组而不冒充第二个独立译对。俄文署名、词偶标题与汉译外括号不并入对应文本；原例组完整归档保留。

仅是教材整例级对应，不是逐句/逐词对齐，不证明翻译充分或语言学标签正确。含词偶对照、教学改写及ср.插语，原作出处尚未全核，跨章重复未去重。本层与先前22目标中的18组分版列报，不能据此声称自然平行语料已完成。

每条记录保留原来源状态，原ready与模型候选分别计量，隔离不解除，未加入训练池。俄语没有汉译的例证可以供原文检索，不能充作平行句。源偏移指向原转录，候选文本仅重放既有编辑。若旧编辑将未变俄文及改变的汉译一起登记，只裁去逐字相同的首尾文本后投影实际变更；完整旧编辑及裁剪位置另存source_edit_projection。实际变更跨语言范围或边界插入仍拒绝，不修改原编校日志。
''','utf8')
    m=dict(schema_version=1,unnumbered_manifest_sha256=fsh(examples/'manifest.json'),review_sha256=fsh(review_path),statistics=dict(pairs=len(pairs),examples_with_pairs=len({p['example_id']for p in pairs}),russian_only_examples=len(review['russian_only_examples'])),files={p.name:fsh(p)for p in output.iterdir()if p.is_file()});write(output/'manifest.json',m);return m

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,default=WORK/'research_exports/aspect_editorial_candidate_20261023_002');p.add_argument('--examples',type=Path,default=WORK/'research_exports/aspect_unnumbered_examples_20261024_001');p.add_argument('--review',type=Path,default=WORK/'reviews/unnumbered_parallel_review_20261024_001.json');p.add_argument('--output',type=Path,default=WORK/'research_exports/aspect_unnumbered_parallel_20261024_001');a=p.parse_args();print(json.dumps(build(a.candidate,a.examples,a.review,a.output)['statistics']))
