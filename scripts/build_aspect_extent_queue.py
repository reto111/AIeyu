"""Enumerate boundary-review contexts without certifying example boundaries."""
from __future__ import annotations
import argparse,json,re,shutil
from collections import Counter,defaultdict
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path
from build_aspect_example_index import bindings,connect,fsh,materialize,pages_for,read,replay_span,tsh,write
from build_aspect_example_extents import verified_files

def build(candidate,index,extents,output):
    candidate,index,extents,output=map(Path,(candidate,index,extents,output))
    if output.exists():raise FileExistsError('Immutable boundary queue')
    im=verified_files(index);verified_files(extents)
    if im['source_candidate_manifest_sha256']!=fsh(candidate/'manifest.json'):raise ValueError('Index source mismatch')
    _,anchors,_,_=materialize(candidate)
    if anchors!=[json.loads(s)for s in (index/'examples.jsonl').read_text('utf8').splitlines()]:raise ValueError('Stale anchors')
    em=read(extents/'manifest.json')
    if em['source_pins']['index_manifest_sha256']!=fsh(index/'manifest.json'):raise ValueError('Extent source mismatch')
    reviewed={x['example_id']for x in map(json.loads,(extents/'extents.jsonl').read_text('utf8').splitlines())}
    groups=defaultdict(list)
    for x in anchors:groups[x['source_unit']].append(x)
    queue=[]
    with closing(connect(candidate/'aspect_reference.sqlite'))as c:
        for code,items in sorted(groups.items()):
            unit=c.execute('select * from chunks where code=?',(code,)).fetchone();raw=unit['body'];spans=bindings(c,unit)
            sec=c.execute('select * from aspect_candidate_sections where code=?',(code,)).fetchone();edits=json.loads(sec['metadata_json'])['edits']
            for i,x in enumerate(items):
                limit=items[i+1]['source_start']if i+1<len(items)else len(raw)
                tail=raw[x['source_end']:limit];paragraphs=[p for p in tail.strip().split('\n\n')if p.strip()];first=paragraphs[0]if paragraphs else''
                flags=[]
                if not x['contains_cjk']and x['contains_cyrillic']and paragraphs:flags.append('russian_anchor_without_cjk_with_following_paragraphs')
                if re.match(r'^[—–-]',first):flags.append('following_paragraph_starts_dialogue_dash')
                if first.startswith(('“','「','『','"')):flags.append('following_paragraph_starts_quote')
                if len(x['page_evidence'])>1:flags.append('anchor_crosses_pdf_pages')
                if re.search(r'\[PDF\d+脚注',tail):flags.append('later_appended_footnote_in_context')
                candidate_context,context_edits=replay_span(raw,x['source_start'],limit,edits)
                queue.append(dict(example_id=x['example_id'],source_unit=code,state=x['state'],already_reviewed_in_22_target_layer=x['example_id']in reviewed,source_start=x['source_start'],anchor_source_end=x['source_end'],context_source_end=limit,source_anchor=x['source_text'],following_source_paragraphs=paragraphs,source_context_until_next_anchor=raw[x['source_start']:limit],source_context_sha256=tsh(raw[x['source_start']:limit]),candidate_context_until_next_anchor=candidate_context,context_edits=context_edits,page_evidence=pages_for(spans,x['source_start'],limit),anchor_page_evidence=x['page_evidence'],following_paragraph_count=len(paragraphs),review_flags=flags,boundary_status='not_decided_by_queue',warning_zh='后续语境可能含作者分析、邻接标题或附后脚注；截止下一编号不是完整例边界。'))
    if len(queue)!=1453 or len(reviewed)!=22 or not reviewed<={x['example_id']for x in queue}:raise ValueError('Queue coverage mismatch')
    stats=dict(anchor_paragraphs=len(queue),units_with_anchors=len(groups),already_reviewed=22,boundaries_not_reviewed=1431,states=dict(Counter(x['state']for x in queue)),unreviewed_flags=dict(Counter(flag for x in queue if not x['already_reviewed_in_22_target_layer']for flag in x['review_flags'])),anchors_with_following_paragraphs=sum(bool(x['following_source_paragraphs'])for x in queue))
    output.mkdir(parents=True)
    (output/'queue.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n'for x in queue),'utf8')
    write(output/'structure_counts.json',stats);shutil.copy2(Path(__file__),output/Path(__file__).name)
    (output/'README.md').write_text('''# 1453编号锚段的边界审核队列

这是一份机械结构清点，不决定完整例句边界。每条保留原锚段、直到下一同节编号之前的完整原/候选语境、页证据及编辑；这段语境可能含作者分析、标题和移至节末的脚注，禁止当作完整例句或新语料句数。

标记供人工/模型逐条定位：俄文首段无汉字且有后段、下一段以对话破折号/引号开始、跨页及附后脚注。标记不保证例句残缺，未标记也不保证完整；4条汉语例不因无俄语自动判缺。现有22目标的边界审核单列，其余1431仍待核，未从结构特征自动批准。

队列含117隔离锚段，作为研究归档；本文件不为其提供默认RAG查询或解除隔离。允许1336锚段仍须区分原ready269与候选1067，不能将档案全集直接交给学生端。每完整单元的复核决定另存新记录，原索引和现有22例层不改。
''','utf8')
    m=dict(created_at=datetime.now(timezone.utc).isoformat(),source_pins=dict(candidate_manifest_sha256=fsh(candidate/'manifest.json'),index_manifest_sha256=fsh(index/'manifest.json'),reviewed_extent_manifest_sha256=fsh(extents/'manifest.json')),statistics=stats,automatic_boundary_decisions=0,files={p.name:fsh(p)for p in sorted(output.iterdir())if p.is_file()});write(output/'manifest.json',m);return m

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['candidate','index','extents','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.candidate,a.index,a.extents,a.output),ensure_ascii=False,indent=2))
