"""Inventory text outside reviewed illustrations; never infer new examples.

Offsets always address chunks.body (raw transcription), not editorial text.
The inventory is a review queue, including theory, citations and formulas.
"""
from __future__ import annotations
import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import json,re
from pathlib import Path
from build_aspect_example_index import connect,bindings,pages_for,replay_span,fsh,tsh,verify_candidate,write
from aspect_corpus_extents import read_collection

WORK=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference'
CYR=re.compile('[А-Яа-яЁё]')
NUMBER=re.compile(r'[（(](\d{1,3})[)）]')

def materialize(candidate,extents):
    cm=verify_candidate(candidate);em,examples=read_collection(extents)
    if em['source_pins']['candidate_manifest_sha256']!=fsh(candidate/'manifest.json'):
        raise ValueError('Candidate/extent version mismatch')
    exclusions=[json.loads(s)for s in(extents/'excluded_anchors.jsonl').read_text('utf8').splitlines()]
    by_unit={};rows=[];units=[];markers=[]
    for row in examples+exclusions:by_unit.setdefault(row['source_unit'],[]).append(row)
    with closing(connect(candidate/'aspect_reference.sqlite'))as c:
        for section in c.execute('select * from aspect_candidate_sections order by code'):
            unit=c.execute('select * from chunks where code=?',(section['code'],)).fetchone()
            raw=unit['body'];meta=json.loads(section['metadata_json']);spans=bindings(c,unit)
            occupied=sorted((r['source_start'],r['source_end'],r['example_id'])for r in by_unit.get(unit['code'],[]))
            end=0
            for lo,hi,_ in occupied:
                if not end<=lo<hi<=len(raw):raise ValueError('Overlapping/out-of-range illustration')
                end=hi
            gaps=[];cursor=0
            for lo,hi,_ in occupied:
                if cursor<lo:gaps.append((cursor,lo))
                cursor=hi
            if cursor<len(raw):gaps.append((cursor,len(raw)))
            if sum(hi-lo for lo,hi,_ in occupied)+sum(hi-lo for lo,hi in gaps)!=len(raw):raise ValueError('Incomplete partition')
            # Every marker is retained, including author cross-references inside examples.
            for match in NUMBER.finditer(raw):
                owner=next((key for lo,hi,key in occupied if lo<=match.start()<hi),None)
                markers.append(dict(source_unit=unit['code'],source_start=match.start(),number=int(match.group(1)),inside_record=owner,
                    context=raw[max(0,match.start()-35):min(len(raw),match.end()+95)],
                    page_evidence=pages_for(spans,match.start(),match.end()),
                    interpretation='not_assessed_marker_may_be_cross_reference'))
            number=0;unit_rows=[]
            for lo,hi in gaps:
                text=raw[lo:hi]
                for para in re.finditer(r'[^\n]+(?:\n(?!\n)[^\n]+)*',text):
                    start=lo+para.start();stop=lo+para.end();source=raw[start:stop]
                    if not source.strip():continue
                    number+=1;edited,edits=replay_span(raw,start,stop,meta['edits'])
                    flags=[]
                    cyr_count=len(CYR.findall(source))
                    if cyr_count:flags.append('contains_cyrillic')
                    if re.match(r'^\s*[А-Яа-яЁё—–«*]',source):flags.append('cyrillic_or_dialogue_at_start')
                    if NUMBER.search(source):flags.append('parenthesis_number_in_residual')
                    if any(x in source for x in ['例如','如：','例句','比较','ср.']):flags.append('illustration_or_comparison_cue')
                    if '\t'in source or '|'in source:flags.append('possible_table_delimiter')
                    if '[PDF'in source:flags.append('transcription_footnote_or_page_note')
                    row=dict(residual_id=f"{unit['code']}.residual.{number:03}",source_unit=unit['code'],unit_title=unit['title'],state=section['state'],
                        source_start=start,source_end=stop,source_text=source,source_text_sha256=tsh(source),candidate_text=edited,candidate_text_sha256=tsh(edited),
                        source_unit_sha256=tsh(raw),candidate_unit_sha256=tsh(section['body']),edits=edits,page_evidence=pages_for(spans,start,stop),
                        flags=flags,cyrillic_characters=cyr_count,review_status='unreviewed_structural_queue',is_confirmed_example=False,
                        source_scope_eligible_original=section['state']=='original_source_ready',source_scope_eligible_with_candidates=section['state']!='withheld',
                        automatic_semantic_classification=False)
                    if not row['page_evidence']:raise ValueError('Unbound residual')
                    if any(start<y and stop>x for x,y,_ in occupied):raise ValueError('Residual overlaps illustration')
                    rows.append(row);unit_rows.append(row)
            units.append(dict(source_unit=unit['code'],state=section['state'],reviewed_or_excluded_intervals=len(occupied),
                residual_paragraphs=len(unit_rows),residual_cyrillic_paragraphs=sum(r['cyrillic_characters']>0 for r in unit_rows),
                source_characters=len(raw),covered_characters=sum(hi-lo for lo,hi,_ in occupied),gap_characters=sum(hi-lo for lo,hi in gaps),
                source_partition_verified=True))
    return rows,units,markers

def build(candidate,extents,output):
    candidate=candidate.resolve();extents=extents.resolve();output=output.resolve()
    if output.exists():raise FileExistsError('Immutable inventory; use a new version')
    rows,units,markers=materialize(candidate,extents);output.mkdir(parents=True)
    for name,data in [('residual_paragraphs.jsonl',rows),('source_units.jsonl',units),('parenthesis_markers.jsonl',markers)]:
        (output/name).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n'for x in data),'utf8')
    statistics=dict(source_units=len(units),residual_paragraphs=len(rows),cyrillic_residual_paragraphs=sum(r['cyrillic_characters']>0 for r in rows),
        flags=dict(Counter(f for r in rows for f in r['flags'])),states=dict(Counter(r['state']for r in rows)),
        parenthesis_markers=len(markers),markers_outside_classified_extents=sum(r['inside_record']is None for r in markers),
        units_without_classified_numbered_examples=sum(u['reviewed_or_excluded_intervals']==0 for u in units),
        automatically_added_examples=0,independently_reviewed_examples=0)
    (output/'README.md').write_text('''# 编号例组之外的结构清点队列

这是100理论单元中已核例组及作者分析排除区间之外的原转录段落清点，不是新增例句库。含理论、词表、引用、脚注和真正的无编号例，全部尚未人工分类。俄文字母、数字括号、比较提示和表格分隔符仅为检索线索；未标记也不等于无例证。

原文偏移、候选编辑和页证据逐项保存。每个单元的已分类区间与余部构成无重叠的全字符分区；段落队列省去分隔空行。数字标记另外列出，可能是编号、回指或公式，禁止直接加到例句数。

本队列不接查询入口，包含隔离节，不能整体导入练习或RAG。模型候选与原转录分别保存，不自动标注时体/对齐或确认翻译。原1453锚段全分类不代表全书所有例证已穷尽。
''','utf8')
    manifest=dict(schema_version=1,created_at=datetime.now(timezone.utc).isoformat(),edition=output.name,
        candidate_manifest_sha256=fsh(candidate/'manifest.json'),extent_manifest_sha256=fsh(extents/'manifest.json'),statistics=statistics,
        inventory_only=True,files={p.name:fsh(p)for p in output.iterdir()if p.is_file()})
    write(output/'manifest.json',manifest);return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,default=WORK/'research_exports/aspect_editorial_candidate_20261023_002');p.add_argument('--extents',type=Path,default=WORK/'research_exports/aspect_corpus_extents_20261023_044');p.add_argument('--output',type=Path,default=WORK/'research_exports/aspect_residual_inventory_20261024_001');a=p.parse_args()
    print(json.dumps(build(a.candidate,a.extents,a.output)['statistics'],ensure_ascii=False,indent=2))
