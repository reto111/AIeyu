"""Build only explicitly reviewed unnumbered spans outside numbered extents."""
import argparse,json,shutil
from pathlib import Path
from contextlib import closing
from collections import Counter
from build_aspect_example_index import connect,bindings,pages_for,replay_span,fsh,tsh,write,verify_candidate
from build_aspect_table_inventory import read_inventory
WORK=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference'

def materialize(candidate,inventory,review):
    verify_candidate(candidate);im,residuals=read_inventory(inventory)
    if review['candidate_manifest_sha256']!=fsh(candidate/'manifest.json')or review['inventory_manifest_sha256']!=fsh(inventory/'manifest.json'):raise ValueError('Review version mismatch')
    lookup={r['residual_id']:r for r in residuals};rows=[];ids=set();intervals={}
    with closing(connect(candidate/'aspect_reference.sqlite'))as c:
        for d in review['records']:
            rid=d['residual_id'];r=lookup[rid];lo=d['source_start'];hi=d['source_end'];key=d['example_id']
            if key in ids:raise ValueError('Duplicate example ID')
            ids.add(key)
            if not r['source_start']<=lo<hi<=r['source_end']:raise ValueError('Span outside residual')
            for a,b in intervals.setdefault(r['source_unit'],[]):
                if lo<b and hi>a:raise ValueError('Overlapping reviewed spans')
            intervals[r['source_unit']].append((lo,hi))
            unit=c.execute('select * from chunks where code=?',(r['source_unit'],)).fetchone()
            section=c.execute('select * from aspect_candidate_sections where code=?',(r['source_unit'],)).fetchone()
            raw=unit['body'];text=raw[lo:hi]
            if tsh(text)!=d['source_text_sha256']or text!=d['source_text']:raise ValueError('Stale reviewed span')
            spans=bindings(c,unit);pages=pages_for(spans,lo,hi)
            if {p['pdf_page']for p in pages}!=set(d['visually_checked_pdf_pages']):raise ValueError('Page review mismatch')
            edited,edits=replay_span(raw,lo,hi,json.loads(section['metadata_json'])['edits'])
            rows.append(dict(example_id=key,record_kind='reviewed_unnumbered_textbook_illustration',source_residual_id=rid,source_unit=r['source_unit'],state=r['state'],
                source_start=lo,source_end=hi,source_text=text,source_text_sha256=tsh(text),candidate_text=edited,candidate_text_sha256=tsh(edited),
                page_evidence=pages,edits=edits,context_source_start=r['source_start'],context_source_end=r['source_end'],source_context=r['source_text'],
                candidate_context=r['candidate_text'],context_page_evidence=r['page_evidence'],boundary_reason_zh=d['boundary_reason_zh'],
                illustration_structure=d['illustration_structure'],eligible_original=r['state']=='original_source_ready',eligible_with_candidates=r['state']!='withheld',
                independent_review=False,semantic_labels_assessed=False,sentence_alignment_assessed=False,natural_corpus_sample=False,
                context_includes_author_analysis=True))
    return rows

def build(candidate,inventory,review_path,output):
    if output.exists():raise FileExistsError('Immutable unnumbered collection')
    review=json.loads(review_path.read_text('utf8'));rows=materialize(candidate,inventory,review);output.mkdir(parents=True)
    (output/'examples.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in rows),'utf8')
    shutil.copy2(Path(__file__).with_name('aspect_unnumbered_examples.py'),output/'aspect_unnumbered_examples.py')
    (output/'README.md').write_text('''# 无编号及行内例证：明确片段补充层

仅收审核文件明确圈定、且在已核编号例组之外的片段；来源偏移指向原转录正文，候选文本重放既有编校。本层与1453编号例组、10张表分别计量，不把三类数量相加当成自然语料句数。

比较组可能含多句、多个署名作品、教学改写和括号释义。同章/跨章重复未去重。原文中的ср.、义项上标以及无汉译原样保留，不补翻译。context字段含作者分析；引用例文本时用source_text或candidate_text，不能把context冒充纯例文。

python aspect_unnumbered_examples.py verify
python aspect_unnumbered_examples.py list --include-candidates
python aspect_unnumbered_examples.py show --id ID --include-candidates

默认只返回原ready，显式候选可加模型编校来源，隔离任何模式不返回。这里只核范围，未作语义/逐句对齐标注、独立专家评定或原作出处全核。余部材料角色分类与行内例抽取分别计量，不称全书无编号例穷尽。
''','utf8')
    stats=dict(records=len(rows),states=dict(Counter(r['state']for r in rows)),eligible_original=sum(r['eligible_original']for r in rows),eligible_with_candidates=sum(r['eligible_with_candidates']for r in rows),source_pdf_pages=len({p['pdf_page']for r in rows for p in r['page_evidence']}))
    m=dict(schema_version=1,candidate_manifest_sha256=fsh(candidate/'manifest.json'),inventory_manifest_sha256=fsh(inventory/'manifest.json'),review_sha256=fsh(review_path),statistics=stats,files={p.name:fsh(p)for p in output.iterdir()if p.is_file()});write(output/'manifest.json',m);return m

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,default=WORK/'research_exports/aspect_editorial_candidate_20261023_002');p.add_argument('--inventory',type=Path,default=WORK/'research_exports/aspect_residual_inventory_20261024_001');p.add_argument('--review',type=Path,default=WORK/'reviews/unnumbered_boundary_review_20261024_001.json');p.add_argument('--output',type=Path,default=WORK/'research_exports/aspect_unnumbered_examples_20261024_001');a=p.parse_args();print(json.dumps(build(a.candidate,a.inventory,a.review,a.output)['statistics'],ensure_ascii=False))
