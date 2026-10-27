"""Export source paragraphs with explicitly reviewed material roles and span links."""
import argparse,json,csv,shutil
from pathlib import Path
from collections import Counter,defaultdict
from build_aspect_example_index import fsh,write
from build_aspect_table_inventory import read_inventory
from aspect_unnumbered_examples import read_collection as read_examples

def materialize(inventory,role_path,examples,tables):
    _,source=read_inventory(inventory);review=json.loads(role_path.read_text('utf8'))
    if review['inventory_manifest_sha256']!=fsh(inventory/'manifest.json'):raise ValueError('Role inventory version mismatch')
    roles={r['residual_id']:r for r in review['records']}
    if len(roles)!=len(review['records'])or set(roles)!={r['residual_id']for r in source}:raise ValueError('Incomplete role partition')
    _,illustrations=read_examples(examples);links=defaultdict(list);tablelinks=defaultdict(list)
    for r in illustrations:links[r['source_residual_id']].append(r['example_id'])
    tm=json.loads((tables/'manifest.json').read_text('utf8'))
    for rel,h in tm['files'].items():
        path=(tables/rel).resolve()
        if not path.is_relative_to(tables.resolve())or fsh(path)!=h:raise ValueError('Table package mismatch')
    for r in map(json.loads,(tables/'tables.jsonl').read_text('utf8').splitlines()):tablelinks[r['source_residual_id']].append(r['table_id'])
    if not(set(links)|set(tablelinks))<=set(roles):raise ValueError('Unknown linked paragraph')
    rows=[]
    for r in source:
        role=roles[r['residual_id']]
        for key in ['source_unit','source_start','source_end','source_text_sha256','state','page_evidence']:
            if r[key]!=role[key]:raise ValueError('Stale role source binding')
        row=dict(r);row.update(paragraph_role=role['paragraph_role'],role_review_note_zh=role['note_zh'],role_review_kind=role.get('review_kind','same_assistant_existing_review'),extracted_illustration_ids=links[r['residual_id']],table_ids=tablelinks[r['residual_id']],review_status='material_role_reviewed_only',all_inline_illustrations_extracted=False,independent_review=False,semantic_truth_assessed=False)
        rows.append(row)
    return rows

def build(inventory,role_path,examples,tables,output):
    if output.exists():raise FileExistsError('Immutable material roles collection')
    rows=materialize(inventory,role_path,examples,tables);output.mkdir(parents=True)
    (output/'paragraphs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in rows),'utf8')
    with(output/'paragraphs.tsv').open('w',encoding='utf8',newline='')as stream:
        w=csv.writer(stream,delimiter='\t');w.writerow(['residual_id','source_unit','state','paragraph_role','pdf_pages','extracted_illustration_ids','table_ids','source_text','candidate_text'])
        for r in rows:w.writerow([r['residual_id'],r['source_unit'],r['state'],r['paragraph_role'],','.join(str(p['pdf_page'])for p in r['page_evidence']),','.join(r['extracted_illustration_ids']),','.join(r['table_ids']),r['source_text'],r['candidate_text']])
    shutil.copy2(Path(__file__).with_name('aspect_material_roles.py'),output/'aspect_material_roles.py')
    (output/'README.md').write_text('''# 教材余段材料角色与例证定位

1333个余段的材料角色与原转录、候选正文、原始偏移、页证据同存。角色来自同一助手逐段阅读，按作者论述、例句混合段、词项、公式、对比表及脚注等区分，不是体意义、翻译或独立专家金标。原结构队列保持冻结。

extracted_illustration_ids与table_ids指向明确圈定的补充例组和对比表；空列表只表示此版未链接，不表示段内无例句。所有all_inline_illustrations_extracted均为false，不据材料角色推算自然语料句数或频率。source_text是归档转录，candidate_text只重放既有编校；引用必须检查原页及版本。

python -X utf8 aspect_material_roles.py verify
python -X utf8 aspect_material_roles.py stats --include-candidates
python -X utf8 aspect_material_roles.py search --text 结果存在 --include-candidates
python -X utf8 aspect_material_roles.py show --id aspect.ch14.s03.03.residual.008 --include-candidates

默认仅原ready，显式候选才返回模型候选；隔离记录归档但任何查询均排除。search为字面匹配，不是自然问题RAG。list/search总数是当前筛选内段落数，分页不改变统计分母。程序只读且不联网。
''','utf8')
    stats=dict(paragraphs=len(rows),units=len({r['source_unit']for r in rows}),states=dict(Counter(r['state']for r in rows)),roles=dict(Counter(r['paragraph_role']for r in rows)),linked_illustration_groups=sum(len(r['extracted_illustration_ids'])for r in rows),linked_tables=sum(len(r['table_ids'])for r in rows))
    m=dict(schema_version=1,inventory_manifest_sha256=fsh(inventory/'manifest.json'),role_review_sha256=fsh(role_path),examples_manifest_sha256=fsh(examples/'manifest.json'),tables_manifest_sha256=fsh(tables/'manifest.json'),statistics=stats,files={p.name:fsh(p)for p in output.iterdir()if p.is_file()});write(output/'manifest.json',m);return m

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inventory',type=Path,required=True);p.add_argument('--roles',type=Path,required=True);p.add_argument('--examples',type=Path,required=True);p.add_argument('--tables',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(build(a.inventory,a.roles,a.examples,a.tables,a.output)['statistics'],ensure_ascii=False))
