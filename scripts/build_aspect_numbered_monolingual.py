"""Build separately reviewed monolingual numbered illustrations without inventing translations."""
import argparse,csv,json,re,shutil
from pathlib import Path
from contextlib import closing
from build_aspect_example_index import fsh,tsh,verify_candidate,connect,bindings,pages_for,write
from build_aspect_unnumbered_parallel import replay_language_span
from aspect_numbered_parallel import read_collection

def materialize(candidate,extents,parallel,review):
    verify_candidate(candidate)
    manifest=json.loads((extents/'manifest.json').read_text('utf8'))
    for rel,h in manifest['files'].items():
        if fsh(extents/rel)!=h:raise ValueError('Changed numbered payload')
    pins=dict(candidate_manifest_sha256=fsh(candidate/'manifest.json'),numbered_manifest_sha256=fsh(extents/'manifest.json'),parallel_manifest_sha256=fsh(parallel/'manifest.json'))
    if review['source_pins']!=pins:raise ValueError('Version mismatch')
    _,paired=read_collection(parallel);paired_ids={r['example_id']for r in paired}
    source=list(map(json.loads,(extents/'examples.jsonl').read_text('utf8').splitlines()));lookup={r['example_id']:r for r in source};seen=set();out=[]
    with closing(connect(candidate/'aspect_reference.sqlite'))as db:
        for d in review['records']:
            key=d['example_id']
            if key not in lookup or key in seen or key in paired_ids:raise ValueError('Unknown, duplicate or already paired group')
            seen.add(key);r=lookup[key]
            if r['state']=='withheld':raise ValueError('Withheld example')
            if d['source_text_sha256']!=r['source_text_sha256']:raise ValueError('Stale reviewed group')
            if set(d['visually_checked_pdf_pages'])!={p['pdf_page']for p in r['page_evidence']}:raise ValueError('Incomplete group page review')
            unit=db.execute('select * from chunks where code=?',(r['source_unit'],)).fetchone();section=db.execute('select * from aspect_candidate_sections where code=?',(r['source_unit'],)).fetchone();raw=unit['body'];edits=json.loads(section['metadata_json'])['edits']
            if tsh(raw)!=r['source_unit_sha256']or tsh(section['body'])!=r['candidate_unit_sha256']or raw[r['source_start']:r['source_end']]!=r['source_text']:raise ValueError('Stale source unit')
            used=[]
            def span(s,role):
                a,b=s['source_start'],s['source_end']
                if not r['source_start']<=a<b<=r['source_end']or tsh(raw[a:b])!=s['source_text_sha256']:raise ValueError('Invalid component range or text')
                if any(a<y and b>x for x,y in used):raise ValueError('Overlapping components')
                used.append((a,b));text=raw[a:b]
                if role=='ru'and(not re.search('[А-Яа-яЁё]',text)or re.search('[\u3400-\u9fff]',text)):raise ValueError('Invalid Russian component')
                if role=='zh'and(not re.search('[\u3400-\u9fff]',text)or re.search('[А-Яа-яЁё]',text)):raise ValueError('Invalid Chinese component')
                value,selected,projection=replay_language_span(raw,a,b,edits)
                result=dict(role=role,source_start=a,source_end=b,source_text=text,candidate_text=value,edits=selected,page_evidence=pages_for(bindings(db,unit),a,b))
                if projection:result['source_edit_projection']=projection
                return result
            lang=d['language']
            if lang not in ['ru','zh']:raise ValueError('Unknown language')
            body=span(d['component'],lang);metadata=[]
            for s in d['metadata']:
                if s['role']not in ['book_marker','source_attribution']:raise ValueError('Unknown metadata role')
                metadata.append(span(s,s['role']))
            cursor=r['source_start'];gaps=[]
            for a,b in sorted(used):
                if cursor<a:gaps.append(dict(source_start=cursor,source_end=a,source_text=raw[cursor:a]))
                cursor=b
            if cursor<r['source_end']:gaps.append(dict(source_start=cursor,source_end=r['source_end'],source_text=raw[cursor:r['source_end']]))
            if any(re.search('[А-Яа-яЁё\u3400-\u9fff]',g['source_text'])for g in gaps):raise ValueError('Unaccounted language-bearing text')
            out.append(dict(example_id=key,source_unit=r['source_unit'],state=r['state'],source_text=r['source_text'],candidate_text=r['candidate_text'],source_start=r['source_start'],source_end=r['source_end'],page_evidence=r['page_evidence'],language=lang,language_components=[body],pairs=[],metadata=metadata,unassigned_formatting_ranges=gaps,source_unit_sha256=r['source_unit_sha256'],candidate_unit_sha256=r['candidate_unit_sha256'],source_unit_cautions=r['external_source_cautions'],caution_scope='inherited_unit_notes_not_individual_quote_verification',review_note_zh=d['review_note_zh'],counterpart_present_in_group=False,independent_review=False,natural_corpus_sample=False))
    pending=[r['example_id']for r in source if r['example_id']not in seen|paired_ids]
    return out,pending

def build(candidate,extents,parallel,review_path,output):
    if output.exists():raise FileExistsError('Immutable monolingual package')
    review=json.loads(review_path.read_text('utf8'));rows,pending=materialize(candidate,extents,parallel,review);output.mkdir(parents=True)
    (output/'groups.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in rows),'utf8');write(output/'unreviewed_after_both_layers.json',pending)
    with(output/'components.tsv').open('w',encoding='utf8',newline='')as stream:
        writer=csv.writer(stream,delimiter='\t');writer.writerow(['example_id','state','language','source_text','candidate_text'])
        for r in rows:
            c=r['language_components'][0];writer.writerow([r['example_id'],r['state'],r['language'],c['source_text'],c['candidate_text']])
    shutil.copy2(review_path,output/'review.json');shutil.copy2(Path(__file__).with_name('aspect_numbered_parallel.py'),output/'aspect_numbered_parallel.py')
    ready=[r for r in rows if r['state']=='original_source_ready'];stats=dict(reviewed_groups=len(rows),component_correspondences=0,eligible_original_groups=len(ready),eligible_original_pairs=0,eligible_with_candidates_groups=len(rows),unreviewed_groups=len(pending),single_language_counts={lang:sum(r['language']==lang for r in rows)for lang in ['ru','zh']},independent_annotations=0)
    (output/'README.md').write_text('# 编号单语例证\n\n本层单列原组中仅有一种语言的例证，pairs为空，不补译、不跨编号制造句对。保留整组、实际正文范围、署名、尖括号语境和原页。与固定双语041层来源ID不重合；两层覆盖后剩余清单不是本层自身双语待办。默认仅原ready，候选须显式启用。独立评阅0，不是自然语料频次或语义金标。\n\n本包使用标准库只读入口：`python -X utf8 aspect_numbered_parallel.py stats --include-candidates`，全文`show --id 来源ID --include-candidates`。显示component_correspondences=0符合单语性质。\n','utf8')
    m=dict(schema_version=1,collection_kind='monolingual_numbered_illustrations',source_pins=review['source_pins'],review_sha256=fsh(review_path),statistics=stats,files={p.name:fsh(p)for p in sorted(output.iterdir())if p.is_file()});write(output/'manifest.json',m);return m

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['candidate','extents','parallel','review','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.candidate,a.extents,a.parallel,a.review,a.output)['statistics']))
