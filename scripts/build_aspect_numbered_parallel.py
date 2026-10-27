"""Build a partial, explicitly reviewed language layer for numbered groups."""
import argparse,csv,json,re,shutil
from pathlib import Path
from contextlib import closing
from build_aspect_example_index import fsh,tsh,verify_candidate,connect,bindings,pages_for,write
from build_aspect_unnumbered_parallel import replay_language_span

def materialize(candidate,extents,review):
    verify_candidate(candidate);manifest=json.loads((extents/'manifest.json').read_text('utf8'))
    for rel,h in manifest['files'].items():
        if fsh(extents/rel)!=h:raise ValueError('Changed numbered payload')
    if review['source_pins']!={'candidate_manifest_sha256':fsh(candidate/'manifest.json'),'numbered_manifest_sha256':fsh(extents/'manifest.json')}:raise ValueError('Version mismatch')
    rows=list(map(json.loads,(extents/'examples.jsonl').read_text('utf8').splitlines()));lookup={r['example_id']:r for r in rows};seen=set();out=[]
    with closing(connect(candidate/'aspect_reference.sqlite'))as db:
        for d in review['records']:
            key=d['example_id']
            if key in seen or key not in lookup:raise ValueError('Duplicate or unknown example')
            seen.add(key);r=lookup[key]
            if r['state']=='withheld':raise ValueError('Withheld example')
            if d['source_text_sha256']!=r['source_text_sha256']:raise ValueError('Stale reviewed group')
            if set(d['visually_checked_pdf_pages'])!={p['pdf_page']for p in r['page_evidence']}:raise ValueError('Incomplete group page review')
            unit=db.execute('select * from chunks where code=?',(r['source_unit'],)).fetchone();section=db.execute('select * from aspect_candidate_sections where code=?',(r['source_unit'],)).fetchone();raw=unit['body'];edits=json.loads(section['metadata_json'])['edits']
            if tsh(raw)!=r['source_unit_sha256']or tsh(section['body'])!=r['candidate_unit_sha256']or raw[r['source_start']:r['source_end']]!=r['source_text']:raise ValueError('Stale source unit')
            used=[];ru_ranges=[];metadata_ranges=[]
            def span(s,role):
                a,b=s['source_start'],s['source_end']
                if not r['source_start']<=a<b<=r['source_end']or tsh(raw[a:b])!=s['source_text_sha256']:raise ValueError('Invalid component range or text')
                overlaps=any(a<y and b>x for x,y in used)
                if overlaps:
                    allowed=d.get('allow_metadata_inside_russian')is True and role in ['word_form_comparison','editor_context']and any(x<=a<b<=y for x,y in ru_ranges)and not any(a<y and b>x for x,y in metadata_ranges)
                    if not allowed:raise ValueError('Overlapping components')
                used.append((a,b));text=raw[a:b]
                if role=='ru':ru_ranges.append((a,b))
                elif role not in ['zh']:metadata_ranges.append((a,b))
                if role=='ru'and(not re.search('[А-Яа-яЁё]',text)or re.search('[\u3400-\u9fff]',text)):raise ValueError('Invalid Russian component')
                if role=='zh'and(not re.search('[\u3400-\u9fff]',text)or re.search('[А-Яа-яЁё]',text)):raise ValueError('Invalid Chinese component')
                value,selected,projection=replay_language_span(raw,a,b,edits)
                result=dict(role=role,source_start=a,source_end=b,source_text=text,candidate_text=value,edits=selected,page_evidence=pages_for(bindings(db,unit),a,b))
                if projection:result['source_edit_projection']=projection
                return result
            pairs=[dict(pair_id=key+f'.pair.{i:02}',ru=span(p['ru'],'ru'),zh=span(p['zh'],'zh'),alignment_level='illustration_component_not_sentence',translation_gold=False)for i,p in enumerate(d['pairs'],1)]
            if not pairs:raise ValueError('No reviewed correspondence')
            metadata=[]
            for s in d['metadata']:
                if s['role']not in ['book_marker','subexample_label','source_attribution','editor_context','word_form_comparison']:raise ValueError('Unknown metadata role')
                metadata.append(span(s,s['role']))
            gaps=[];cursor=r['source_start']
            for a,b in sorted(used):
                if cursor<a:gaps.append(dict(source_start=cursor,source_end=a,source_text=raw[cursor:a]))
                cursor=max(cursor,b)
            if cursor<r['source_end']:gaps.append(dict(source_start=cursor,source_end=r['source_end'],source_text=raw[cursor:r['source_end']]))
            if any(re.search('[А-Яа-яЁё\u3400-\u9fff]',g['source_text'])for g in gaps):raise ValueError('Unaccounted language-bearing text')
            out.append(dict(example_id=key,source_unit=r['source_unit'],state=r['state'],source_text=r['source_text'],candidate_text=r['candidate_text'],page_evidence=r['page_evidence'],source_start=r['source_start'],source_end=r['source_end'],pairs=pairs,metadata=metadata,unassigned_formatting_ranges=gaps,review_note_zh=d['review_note_zh'],independent_review=False,sentence_alignment_assessed=False,translation_accuracy_verified=False,natural_corpus_sample=False))
            if review.get('include_source_metadata'):
                out[-1].update(source_unit_sha256=r['source_unit_sha256'],candidate_unit_sha256=r['candidate_unit_sha256'],source_unit_cautions=r['external_source_cautions'],caution_scope='inherited_unit_notes_not_individual_quote_verification')
            if d.get('allow_metadata_inside_russian'):out[-1]['russian_may_include_marked_metadata']=True
    return out,[r['example_id']for r in rows if r['example_id']not in seen]

def build(candidate,extents,review_path,output):
    if output.exists():raise FileExistsError('Immutable numbered parallel package')
    review=json.loads(review_path.read_text('utf8'));rows,pending=materialize(candidate,extents,review);output.mkdir(parents=True)
    (output/'groups.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in rows),'utf8');write(output/'unreviewed_example_ids.json',pending)
    with(output/'pairs.tsv').open('w',encoding='utf8',newline='')as stream:
        writer=csv.writer(stream,delimiter='\t');writer.writerow(['pair_id','example_id','state','source_ru','source_zh','candidate_ru','candidate_zh'])
        for r in rows:
            for p in r['pairs']:writer.writerow([p['pair_id'],r['example_id'],r['state'],p['ru']['source_text'],p['zh']['source_text'],p['ru']['candidate_text'],p['zh']['candidate_text']])
    shutil.copy2(review_path,output/'review.json');shutil.copy2(Path(__file__).with_name('aspect_numbered_parallel.py'),output/'aspect_numbered_parallel.py')
    pairs=sum(len(r['pairs'])for r in rows);ready=[r for r in rows if r['state']=='original_source_ready']
    (output/'README.md').write_text(f'# 编号例组俄汉对应扩展\n\n本版审核{len(rows)}组、{pairs}个例证组成部分对应，另{len(pending)}组尚未在本扩展层审核。默认{len(ready)}组，候选需显式启用；隔离不返回。a/b分别圈定，对话整段可含多句，不能将对应数量当成自然平行句数。书号、子例标签和署名另存；未分配的仅为排版字符，原组全文保持。\n\n与旧22目标层存在重合，不能把两个版本相加。本层不补译、不确定翻译金标或体意义标签，独立复核0；本批是来源范围审核。默认读取：`python -X utf8 aspect_numbered_parallel.py stats`；显式候选加`--include-candidates`，全文用`show --id 来源ID`。不需网络或原项目即可只读查询；完整构建仍需项目原输入。\n','utf8')
    stats=dict(reviewed_groups=len(rows),component_correspondences=pairs,eligible_original_groups=len(ready),eligible_original_pairs=sum(len(r['pairs'])for r in ready),eligible_with_candidates_groups=len(rows),unreviewed_groups=len(pending),independent_annotations=0)
    m=dict(schema_version=1,source_pins=review['source_pins'],review_sha256=fsh(review_path),statistics=stats,files={p.name:fsh(p)for p in sorted(output.iterdir())if p.is_file()});write(output/'manifest.json',m);return m

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['candidate','extents','review','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.candidate,a.extents,a.review,a.output)['statistics']))
