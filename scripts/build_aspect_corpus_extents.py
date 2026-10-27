"""Combine explicit boundary reviews without promoting source eligibility."""
from __future__ import annotations
import argparse,json,shutil,csv,re
from collections import Counter
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path
from build_aspect_example_index import bindings,connect,fsh,materialize,pages_for,read,replay_span,tsh,write
from build_aspect_example_extents import verified_files

def materialize_corpus(candidate,index,pilot_extents,supplements):
    candidate,index,pilot_extents=map(Path,(candidate,index,pilot_extents));verified_files(index);em=verified_files(pilot_extents)
    pins=dict(candidate_manifest_sha256=fsh(candidate/'manifest.json'),index_manifest_sha256=fsh(index/'manifest.json'),pilot_extent_manifest_sha256=fsh(pilot_extents/'manifest.json'))
    if em['source_pins']['candidate_manifest_sha256']!=pins['candidate_manifest_sha256']or em['source_pins']['index_manifest_sha256']!=pins['index_manifest_sha256']:raise ValueError('Incompatible initial extents')
    _,anchors,_,_=materialize(candidate);lookup={x['example_id']:x for x in anchors};decisions={};manual={}
    for x in map(json.loads,(pilot_extents/'extents.jsonl').read_text('utf8').splitlines()):
        decisions[x['example_id']]=dict(example_id=x['example_id'],source_start=x['source_start'],source_end=x['source_end'],source_text_sha256=x['source_text_sha256'],visually_checked_pdf_pages=[p['pdf_page']for p in x['page_evidence']],boundary_reason_zh=x['boundary_reason_zh'],review_file='initial_extent_layer',review_kind='same_assistant_visual')
    supplement_pins={}
    for path in map(Path,supplements):
        doc=read(path)
        if doc['candidate_manifest_sha256']!=pins['candidate_manifest_sha256']or doc['index_manifest_sha256']!=pins['index_manifest_sha256']:raise ValueError('Supplement source mismatch')
        supplement_pins[path.name]=fsh(path)
        for d in doc.get('manual_additions',[]):
            eid=d['example_id'];code=d['source_unit'];number=d['book_number']
            if eid in lookup or not re.fullmatch(re.escape(code)+r'\.supplement\.'+f'{number:03}'+r'\.\d{2}',eid):raise ValueError('Invalid supplementary anchor ID')
            peers=[x for x in anchors if x['source_unit']==code]
            if not peers:raise ValueError('Unknown supplementary unit')
            lookup[eid]=dict(source_unit=code,source_start=d['source_start'],source_end=d['source_end'],external_source_cautions=peers[0]['external_source_cautions'])
            manual[eid]=d
        for d in doc['records']+doc.get('manual_additions',[]):
            if d['example_id']in decisions:raise ValueError('Duplicate reviewed anchor')
            decisions[d['example_id']]=dict(d,review_file=path.name)
    result=[]
    with closing(connect(candidate/'aspect_reference.sqlite'))as c:
        for eid,d in sorted(decisions.items()):
            if eid not in lookup:raise ValueError('Unknown reviewed anchor')
            x=lookup[eid];code=x['source_unit'];unit=c.execute('select * from chunks where code=?',(code,)).fetchone();raw=unit['body'];section=c.execute('select * from aspect_candidate_sections where code=?',(code,)).fetchone();meta=json.loads(section['metadata_json'])
            start,end=d['source_start'],d['source_end']
            if start!=x['source_start']or not x['source_end']<=end<=len(raw)or tsh(raw[start:end])!=d['source_text_sha256']:raise ValueError('Invalid reviewed extent')
            if any(start<other['source_start']<end for other in anchors if other['source_unit']==code):raise ValueError('Extent swallows next anchor')
            if d['review_kind']!='same_assistant_visual':raise ValueError('Unsupported review provenance')
            pages=pages_for(bindings(c,unit),start,end)
            if [p['pdf_page']for p in pages]!=d['visually_checked_pdf_pages']:raise ValueError('Incomplete visual page list')
            for p in pages:
                if fsh(candidate.resolve().parent.parent/'renders'/f"p{p['pdf_page']:04}.png")!=p['render_sha256']:raise ValueError('Visual page changed')
            text,edits=replay_span(raw,start,end,meta['edits'])
            if eid in manual:
                original_marker=manual[eid]['original_marker']
                if not raw[start:end].startswith(original_marker)or not text.startswith(f"({manual[eid]['book_number']})")or any(other['source_start']<end and other['source_end']>start for other in anchors if other['source_unit']==code):raise ValueError('Supplement marker or indexed overlap mismatch')
            result.append(dict(example_id=eid,source_unit=code,state=section['state'],eligible_original=section['state']=='original_source_ready',eligible_with_candidates=section['state']in('original_source_ready','model_editorial_candidate'),source_start=start,source_end=end,source_text=raw[start:end],source_text_sha256=tsh(raw[start:end]),candidate_text=text,candidate_text_sha256=tsh(text),source_unit_sha256=tsh(raw),candidate_unit_sha256=tsh(section['body']),original_anchor_end=x['source_end'],extends_anchor=end>x['source_end'],paragraph_count=len(raw[start:end].split('\n\n')),page_evidence=pages,edits=edits,external_source_cautions=x['external_source_cautions'],boundary_reason_zh=d['boundary_reason_zh'],boundary_review_file=d['review_file'],reviewed_record_kind='textbook_illustration',review_kind=d['review_kind'],independent_boundary_review=False,sentence_alignment_assessed=False,natural_corpus_sample=False))
            if eid in manual:result[-1].update(manual_numbered_marker_supplement=True,original_marker=manual[eid]['original_marker'],book_number=manual[eid]['book_number'])
    prior_by_unit={}
    for x in sorted(result,key=lambda x:(x['source_unit'],x['source_start'])):
        if x['source_unit']in prior_by_unit and prior_by_unit[x['source_unit']]>x['source_start']:raise ValueError('Reviewed example extents overlap')
        prior_by_unit[x['source_unit']]=x['source_end']
    return result,pins,supplement_pins

def materialize_exclusions(candidate,index,supplements,examples):
    candidate,index=map(Path,(candidate,index));_,anchors,_,_=materialize(candidate);lookup={x['example_id']:x for x in anchors};used={x['example_id']for x in examples};result=[]
    for path in map(Path,supplements):
        doc=read(path)
        if doc['candidate_manifest_sha256']!=fsh(candidate/'manifest.json')or doc['index_manifest_sha256']!=fsh(index/'manifest.json'):raise ValueError('Exclusion source mismatch')
        for d in doc.get('excluded_anchors',[]):
            eid=d['example_id']
            if eid in used or eid not in lookup:raise ValueError('Duplicate or unknown exclusion')
            x=lookup[eid]
            if d['exclusion_kind']!='numbered_author_exposition'or d['review_kind']!='same_assistant_visual':raise ValueError('Unsupported exclusion provenance')
            if d['source_text_sha256']!=x['source_text_sha256']or d['visually_checked_pdf_pages']!=[p['pdf_page']for p in x['page_evidence']]:raise ValueError('Stale exclusion review')
            for p in x['page_evidence']:
                if fsh(candidate.resolve().parent.parent/'renders'/f"p{p['pdf_page']:04}.png")!=p['render_sha256']:raise ValueError('Exclusion image changed')
            used.add(eid);result.append(dict(example_id=eid,source_unit=x['source_unit'],state=x['state'],source_start=x['source_start'],source_end=x['source_end'],source_text=x['source_text'],source_text_sha256=x['source_text_sha256'],page_evidence=x['page_evidence'],exclusion_kind=d['exclusion_kind'],reason_zh=d['reason_zh'],review_file=path.name,independent_review=False))
    return result

def build(candidate,index,pilot_extents,supplements,output):
    output=Path(output)
    if output.exists():raise FileExistsError('Immutable corpus extent collection')
    rows,pins,review_pins=materialize_corpus(candidate,index,pilot_extents,supplements);excluded=materialize_exclusions(candidate,index,supplements,rows);output.mkdir(parents=True)
    (output/'examples.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n'for x in rows),'utf8')
    (output/'excluded_anchors.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n'for x in excluded),'utf8')
    fields=['example_id','source_unit','state','source_start','source_end','paragraph_count','extends_anchor','source_text','candidate_text','boundary_reason_zh']
    with (output/'examples.tsv').open('w',encoding='utf-8-sig',newline='')as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',extrasaction='ignore');w.writeheader();w.writerows(rows)
    for path in map(Path,supplements):shutil.copy2(path,output/path.name)
    for script in [Path(__file__),Path(__file__).with_name('aspect_corpus_extents.py')]:shutil.copy2(script,output/script.name)
    _,all_anchors,_,_=materialize(candidate)
    full_counts=Counter(x['source_unit']for x in all_anchors);reviewed_counts=Counter(x['source_unit']for x in rows if not x.get('manual_numbered_marker_supplement'));classified_counts=reviewed_counts+Counter(x['source_unit']for x in excluded)
    indexed_count=sum(reviewed_counts.values());manual_count=len(rows)-indexed_count;classified=indexed_count+len(excluded)
    stats=dict(reviewed_anchors=len(rows),reviewed_indexed_anchors=indexed_count,manual_numbered_marker_supplements=manual_count,excluded_indexed_anchors=len(excluded),classified_indexed_anchors=classified,unreviewed_anchors=1453-classified,states=dict(Counter(x['state']for x in rows)),extended_anchors=sum(x['extends_anchor']for x in rows),reviewed_source_pdf_pages=len({p['pdf_page']for x in rows for p in x['page_evidence']}),eligible_original=sum(x['eligible_original']for x in rows),eligible_with_candidates=sum(x['eligible_with_candidates']for x in rows),units_with_all_indexed_anchor_boundaries_reviewed={code:count for code,count in sorted(full_counts.items())if classified_counts[code]==count})
    (output/'README.md').write_text('''# 体学完整教材例句范围：累计审核集

累计合并已明确核图的编号例句边界，原文/候选、原偏移、页、编辑和警示分列。只覆盖manifest中的reviewed_anchors，其余仍待审核。每条是教材例证，可能多句、多轮、含译文/署名/编者插语，不是自然语料或逐句对齐金标。

原ready、模型候选与隔离的状态继承来源，不因边界审核而解除隔离。档案JSONL/TSV包含隔离材料；包内入口默认只显示原ready，--include-candidates显式纳入候选，隔离任何模式均不显示。不要将整份档案直接接入学生端。

    python -X utf8 aspect_corpus_extents.py verify
    python -X utf8 aspect_corpus_extents.py list --include-candidates
    python -X utf8 aspect_corpus_extents.py show --id aspect.ch07.s02.example.003.01 --include-candidates

边界均由同一助手核图，不是独立专家审核；不附模型语义标签。各批审核决定只作边界证据，不改变原印库或默认RAG。查询脚本可离线运行，完整复建需显式绑定的项目候选、索引、原22例层、各批审核记录及页图。
''','utf8')
    if manual_count:
        with (output/'README.md').open('a',encoding='utf8')as f:f.write(f'\n本版另含{manual_count}条异常编号的明确补定位，ID用supplement并保留original_marker；不改变旧1453索引。例句记录{len(rows)}＝已核旧索引例句{indexed_count}＋补定位{manual_count}；另{len(excluded)}条已判为作者分析而排除，旧索引未核为{1453-classified}。补定位不是扩段，不并入前一例。\n')
    if excluded:
        with (output/'README.md').open('a',encoding='utf8')as f:f.write('\nexcluded_anchors.jsonl保留被数字正则匹配、实为作者回指分析的段落；这些段落仍在原知识库，不进入本例句集或包内查询。排除是教材话语角色判断，不是源理论正确/错误的裁定。\n')
    m=dict(created_at=datetime.now(timezone.utc).isoformat(),source_pins=pins,review_file_pins=review_pins,statistics=stats,independent_boundary_review=False,files={p.name:fsh(p)for p in sorted(output.iterdir())if p.is_file()});write(output/'manifest.json',m);return m

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['candidate','index','pilot-extents','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--supplement',action='append',type=Path,default=[]);a=p.parse_args();print(json.dumps(build(a.candidate,a.index,a.pilot_extents,a.supplement,a.output),ensure_ascii=False,indent=2))
