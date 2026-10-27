"""Source-bound whole-illustration pairs, separate from sentence alignment."""
from __future__ import annotations
import argparse,csv,json,re,shutil
from contextlib import closing
from datetime import datetime,timezone
from pathlib import Path
from build_aspect_example_index import connect,fsh,read,replay_span,tsh,write
from build_aspect_example_extents import verified_files

def materialize_pairs(candidate,extents,review):
    candidate,extents,review=map(Path,(candidate,extents,review));verified_files(candidate);em=verified_files(extents);r=read(review)
    pins=dict(candidate_manifest_sha256=fsh(candidate/'manifest.json'),extent_manifest_sha256=fsh(extents/'manifest.json'))
    if r['source_pins']!=pins or em['source_pins']['candidate_manifest_sha256']!=pins['candidate_manifest_sha256']:raise ValueError('Incompatible parallel source')
    rows=[json.loads(s)for s in (extents/'extents.jsonl').read_text('utf8').splitlines()];decisions=r['records']
    if len(rows)!=len(decisions) or len({x['example_id']for x in decisions})!=len(decisions) or {x['example_id']for x in rows}!={x['example_id']for x in decisions}:raise ValueError('Pair review coverage mismatch')
    decisions={x['example_id']:x for x in decisions};out=[]
    with closing(connect(candidate/'aspect_reference.sqlite'))as c:
        for x in rows:
            d=decisions[x['example_id']];unit=c.execute('select * from chunks where code=?',(x['source_unit'],)).fetchone();raw=unit['body']
            sec=c.execute('select * from aspect_candidate_sections where code=?',(x['source_unit'],)).fetchone();meta=json.loads(sec['metadata_json'])
            lo,hi=x['source_start'],x['source_end'];text=raw[lo:hi]
            if tsh(raw)!=x['source_unit_sha256'] or tsh(sec['body'])!=x['candidate_unit_sha256'] or tsh(text)!=x['source_text_sha256']:raise ValueError('Stale example extent')
            if sec['state']=='withheld':raise ValueError('Withheld pair source')
            marker=re.match(r'\(\d+\)',text)
            if not marker:raise ValueError('Missing book marker')
            content_start=lo+marker.end()
            while raw[content_start].isspace():content_start+=1
            def span(start,end,role):
                if not lo<=start<end<=hi:raise ValueError('Component outside extent')
                value,edits=replay_span(raw,start,end,meta['edits'])
                return dict(role=role,source_start=start,source_end=end,source_text=raw[start:end],source_text_sha256=tsh(raw[start:end]),candidate_text=value,candidate_text_sha256=tsh(value),edits=edits)
            if d['kind']=='whole_illustration_pair':
                zh=d['chinese_start'];ru_end=zh
                while raw[ru_end-1].isspace():ru_end-=1
                if not content_start<ru_end<=zh<hi or not re.search('[А-Яа-яЁё]',raw[content_start:ru_end]) or re.search('[\u3400-\u9fff]',raw[content_start:ru_end]) or not re.search('[\u3400-\u9fff]',raw[zh:hi]):raise ValueError('Invalid language boundary')
                if d['chinese_opening']!=raw[zh:zh+len(d['chinese_opening'])]:raise ValueError('Chinese opening changed')
                ru=span(content_start,ru_end,'russian_illustration_including_marked_metadata');cn=span(zh,hi,'textbook_chinese_translation');metadata=[]
                for item in d['russian_metadata']:
                    a,b=item['source_start'],item['source_end']
                    if item['role']not in ('source_attribution','editor_context','word_form_comparison'):raise ValueError('Unknown metadata role')
                    if not content_start<=a<b<=ru_end or raw[a:b]!=item['text']:raise ValueError('Invalid Russian metadata')
                    metadata.append(span(a,b,item['role']))
                for a,b in zip(sorted(metadata,key=lambda z:z['source_start']),sorted(metadata,key=lambda z:z['source_start'])[1:]):
                    if a['source_end']>b['source_start']:raise ValueError('Overlapping metadata')
                kind='whole_textbook_illustration_pair'
            elif d['kind']=='chinese_only_in_reviewed_extent':
                if re.search('[А-Яа-яЁё]',text):raise ValueError('Russian material in Chinese-only extent')
                ru=None;cn=span(content_start,hi,'chinese_illustration');metadata=[];kind='no_inline_russian_pair'
            else:raise ValueError('Unknown pairing decision')
            out.append(dict(example_id=x['example_id'],alignment_kind=kind,source_unit=x['source_unit'],state=x['state'],source_unit_sha256=x['source_unit_sha256'],candidate_unit_sha256=x['candidate_unit_sha256'],extent_source_start=lo,extent_source_end=hi,extent_source_text_sha256=x['source_text_sha256'],book_marker=span(lo,lo+marker.end(),'book_example_number'),russian=ru,chinese=cn,russian_metadata=metadata,page_evidence=x['page_evidence'],external_source_cautions=x['external_source_cautions'],review_note_zh=d['review_note_zh'],alignment_review='same_assistant_source_page_and_text_review',independent_alignment_review=False,sentence_alignment=False,translation_accuracy_verified=False,natural_corpus_sample=False,semantic_labels_included=False))
    return out,pins

def build(candidate,extents,review,output):
    output=Path(output)
    if output.exists():raise FileExistsError('Immutable parallel package')
    rows,pins=materialize_pairs(candidate,extents,review);output.mkdir(parents=True)
    (output/'illustrations.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n'for x in rows),'utf8')
    with (output/'illustrations.tsv').open('w',encoding='utf-8-sig',newline='')as f:
        fields=['example_id','alignment_kind','source_unit','russian_source','russian_candidate','chinese_source','chinese_candidate','review_note_zh'];w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader()
        for r in rows:w.writerow(dict(example_id=r['example_id'],alignment_kind=r['alignment_kind'],source_unit=r['source_unit'],russian_source=r['russian']['source_text']if r['russian']else'',russian_candidate=r['russian']['candidate_text']if r['russian']else'',chinese_source=r['chinese']['source_text'],chinese_candidate=r['chinese']['candidate_text'],review_note_zh=r['review_note_zh']))
    shutil.copy2(review,output/'parallel_review.json');shutil.copy2(Path(__file__),output/Path(__file__).name)
    (output/'README.md').write_text('''# 体学22例的整例俄汉对应层

18条俄文例句与本书中文译文按整例对应，4条汉语例在已核范围内没有俄文，不强凑句对。对话可包含多句、多轮，18不是句对总数；尚未做逐句或逐词对齐。这是定向教材例证及译文，不是自然双语平行语料或独立翻译质量金标。

书中编号另存。俄文范围中的署名、来源、编者情境和词形比较分别标记russian_metadata；原俄文范围保留这些字符。不能直接对该范围做纯自然俄语频率统计。标记为情境的“Окно сейчас закрыто”没有对应中文译出；标记为“ср.: строит”的比较插语不是叙事断言。

每段保留原转录/候选编校、全单位原偏移、各自指纹、编辑、页证据及外部异文警示。例(48)中文原译与候选修译分列；候选修译不等于独立专家确认。四条汉语例的俄译可能在别的编号或作者分析中，本包只报告已核范围，不断言全书无对应。

不附已有模型语义标签；其17条例外依据仍属于作者分析，不混入译文。22例边界审核与本次对应判读均由同一助手完成，独立复核0；未改原转录、候选、旧试标或学生数据。
''','utf8')
    stats=dict(reviewed_examples=len(rows),whole_illustration_pairs=sum(x['russian']is not None for x in rows),chinese_only_in_extent=sum(x['russian']is None for x in rows),russian_metadata_spans=sum(len(x['russian_metadata'])for x in rows),sentence_alignment_assessed=False)
    m=dict(created_at=datetime.now(timezone.utc).isoformat(),schema_version=1,source_pins=pins,statistics=stats,independent_alignment_review=False,not_a_natural_frequency_corpus=True,files={p.name:fsh(p)for p in sorted(output.iterdir())if p.is_file()});write(output/'manifest.json',m);return m

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ['candidate','extents','review','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.candidate,a.extents,a.review,a.output),ensure_ascii=False,indent=2))
