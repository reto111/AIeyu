"""Replay separately reviewed textbook example extents; never infer boundaries."""
from __future__ import annotations
import argparse,csv,json,shutil
from collections import Counter
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path
from build_aspect_example_index import (bindings,connect,fsh,materialize,pages_for,
                                       read,replay_span,tsh,write)

def verified_files(directory):
    directory=Path(directory).resolve();manifest=read(directory/'manifest.json')
    for name,pin in manifest['files'].items():
        p=(directory/name).resolve()
        if not p.is_relative_to(directory) or fsh(p)!=pin:raise ValueError('Source package changed')
    return manifest

def materialize_extents(candidate,index,pilot,review):
    candidate,index,pilot=map(Path,(candidate,index,pilot));review=Path(review)
    im=verified_files(index);pm=verified_files(pilot);rm=read(review)
    pins=dict(candidate_manifest_sha256=fsh(candidate/'manifest.json'),index_manifest_sha256=fsh(index/'manifest.json'),pilot_manifest_sha256=fsh(pilot/'manifest.json'))
    if rm['source_pins']!=pins or im['source_candidate_manifest_sha256']!=pins['candidate_manifest_sha256'] or pm['source_pins']['index_manifest_sha256']!=pins['index_manifest_sha256'] or pm['source_pins']['candidate_manifest_sha256']!=pins['candidate_manifest_sha256']:raise ValueError('Incompatible source editions')
    _,anchors,_,_=materialize(candidate);anchors={r['example_id']:r for r in anchors}
    targets=[json.loads(line) for line in (pilot/'annotations.jsonl').read_text('utf8').splitlines()]
    decisions=rm['records']
    if len(decisions)!=len(targets) or len({x['example_id'] for x in decisions})!=len(decisions) or {x['example_id'] for x in decisions}!={x['example_id'] for x in targets}:raise ValueError('Review target coverage mismatch')
    decisions={x['example_id']:x for x in decisions};result=[]
    with closing(connect(candidate/'aspect_reference.sqlite')) as c:
        for target in targets:
            eid=target['example_id'];a=anchors[eid];d=decisions[eid]
            unit=c.execute('select * from chunks where code=?',(a['source_unit'],)).fetchone();raw=unit['body']
            section=c.execute('select * from aspect_candidate_sections where code=?',(a['source_unit'],)).fetchone();meta=json.loads(section['metadata_json'])
            start,end=d['source_start'],d['source_end']
            if section['state']=='withheld' or start!=a['source_start'] or not a['source_end']<=end<=len(raw):raise ValueError('Invalid allowed extent')
            if d['source_text_sha256']!=tsh(raw[start:end]) or target['source_unit_sha256']!=tsh(raw) or target['candidate_unit_sha256']!=tsh(section['body']):raise ValueError('Stale extent review')
            if any(start<other['source_start']<end for other in anchors.values() if other['source_unit']==a['source_unit']):raise ValueError('Extent includes another numbered example')
            tb=target['target_binding']
            if not start<=tb['source_start']<tb['source_end']<=end or raw[tb['source_start']:tb['source_end']]!=target['target']:raise ValueError('Target outside extent')
            spans=bindings(c,unit);pages=pages_for(spans,start,end)
            if d['visually_checked_pdf_pages']!=[p['pdf_page'] for p in pages]:raise ValueError('Visual page coverage mismatch')
            for p in pages:
                render=candidate.resolve().parent.parent/'renders'/f"p{p['pdf_page']:04}.png"
                if fsh(render)!=p['render_sha256']:raise ValueError('Visual render changed')
            if tb['page_evidence']!=pages_for(spans,tb['source_start'],tb['source_end']):raise ValueError('Target page evidence changed')
            candidate_text,edits=replay_span(raw,start,end,meta['edits'])
            contained=[];outside=[]
            for b in target['basis_bindings']:
                if raw[b['source_start']:b['source_end']]!=b['text']:raise ValueError('Stale semantic basis')
                (contained if start<=b['source_start']<b['source_end']<=end else outside).append(b)
            next_anchor=min((x['source_start'] for x in anchors.values() if x['source_unit']==a['source_unit'] and x['source_start']>start),default=len(raw))
            result.append(dict(example_id=eid,record_kind='same_assistant_visually_reviewed_textbook_example_extent',source_unit=a['source_unit'],state=a['state'],source_start=start,source_end=end,source_text=raw[start:end],source_text_sha256=tsh(raw[start:end]),candidate_text=candidate_text,candidate_text_sha256=tsh(candidate_text),source_unit_sha256=tsh(raw),candidate_unit_sha256=tsh(section['body']),original_anchor_end=a['source_end'],extends_anchor=end>a['source_end'],paragraph_count=len(raw[start:end].split('\n\n')),page_evidence=pages,edits=edits,target_binding=tb,basis_bindings_inside_extent=contained,basis_bindings_outside_extent=outside,next_anchor_start=next_anchor,following_source_preview=raw[end:min(end+160,len(raw))],boundary_reason_zh=d['boundary_reason_zh'],layout_note_zh=d['layout_note_zh'],external_source_cautions=a['external_source_cautions'],boundary_reviewed_by='same_assistant',independent_boundary_review=False,language_alignment_assessed=False,semantic_labels_changed=False,not_a_natural_frequency_corpus=True))
    return result,pins

def build(candidate,index,pilot,review,output):
    output=Path(output)
    if output.exists():raise FileExistsError('Immutable extent package; choose another version')
    rows,pins=materialize_extents(candidate,index,pilot,review)
    output.mkdir(parents=True)
    (output/'extents.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),'utf8')
    fields=['example_id','source_unit','state','source_start','source_end','extends_anchor','paragraph_count','source_text','candidate_text','boundary_reason_zh','layout_note_zh']
    with (output/'extents.tsv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',extrasaction='ignore');w.writeheader();w.writerows(rows)
    shutil.copy2(review,output/'boundary_review.json')
    shutil.copy2(Path(__file__),output/Path(__file__).name)
    stats=dict(reviewed_examples=len(rows),anchor_already_complete=sum(not x['extends_anchor'] for x in rows),extended_examples=sum(x['extends_anchor'] for x in rows),cross_page_examples=sum(len(x['page_evidence'])>1 for x in rows),reviewed_pdf_pages=len({p['pdf_page'] for x in rows for p in x['page_evidence']}),basis_quotes_inside=sum(len(x['basis_bindings_inside_extent']) for x in rows),basis_quotes_outside=sum(len(x['basis_bindings_outside_extent']) for x in rows),states=dict(Counter(x['state'] for x in rows)))
    (output/'README.md').write_text('''# 体学既有22试标目标：完整教材例句边界层

本包单独记录22个既有目标在教材中的完整例句范围，同一助手逐页核图；不是专家金标、随机抽样或自然语料。其余1431个编号首段锚点尚未完成这项边界审核，1453不是全书完整例句数。

21例原锚段已覆盖该编号下正文及教材译文；ch06.s01.01例(15)补入俄文回答及两段中文译文，止于下一例(16)之前。ch01.s04.02例(7)跨PDF51–52；ch13.s03.03例(5)/(14)是左右栏对照，各自成例，不按线性邻接合并。中文例句不跨过作者分析去拼接另编号的俄译例句。括号内编者情境及词形比较保留在源范围，但不认定为文学人物直接话语。

原转录、候选编校文本、原单位半开偏移、页/图指纹、编辑及外部异文警示分别保留。目标和39条已有语义依据的位置逐条复核；依据落在例外时另列，不为满足标签而扩入作者论述。边界通过不表示翻译或语义标签正确；语言对齐未完成。原索引、试标和学生数据未改。

复建依赖当前已绑定的候选002、索引002、试标23日001和boundary_review.json；根目录scripts/build_aspect_example_extents.py支持显式路径。TSV为多行带引号字段，请用支持TSV的工具读取，不逐物理行计例数。
''','utf8')
    manifest=dict(created_at=datetime.now(timezone.utc).isoformat(),schema_version=1,source_pins=pins,statistics=stats,provisional=True,independent_boundary_review=False,semantic_labels_changed=False,files={p.name:fsh(p) for p in sorted(output.iterdir()) if p.is_file()})
    write(output/'manifest.json',manifest);return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['candidate','index','pilot','review','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.candidate,a.index,a.pilot,a.review,a.output),ensure_ascii=False,indent=2))
