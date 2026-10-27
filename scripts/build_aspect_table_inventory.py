"""Export explicitly page-reviewed textbook tables, without semantic labels."""
import argparse,csv,json,re
from pathlib import Path
from collections import Counter
from build_aspect_example_index import fsh,tsh,write

WORK=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference'

def read_inventory(root):
    m=json.loads((root/'manifest.json').read_text('utf8'))
    for name,pin in m['files'].items():
        p=(root/name).resolve()
        if not p.is_relative_to(root.resolve())or fsh(p)!=pin:raise ValueError('Inventory file mismatch')
    return m,[json.loads(s)for s in(root/'residual_paragraphs.jsonl').read_text('utf8').splitlines()]

def parse_table(text):
    lines=[x for x in text.splitlines()if x.startswith('|')]
    cells=[[s.strip()for s in x.strip().strip('|').split('|')]for x in lines]
    if len(cells)<3 or any(not re.fullmatch(r':?-+:?',x)for x in cells[1]):raise ValueError('Not a Markdown table')
    if any(len(x)!=len(cells[0])for x in cells):raise ValueError('Ragged table')
    return cells[0],cells[2:]

def materialize(inventory,review):
    m,source=read_inventory(inventory)
    if review['inventory_manifest_sha256']!=fsh(inventory/'manifest.json'):raise ValueError('Review version mismatch')
    lookup={r['residual_id']:r for r in source};tables=[]
    seen=set()
    for decision in review['tables']:
        rid=decision['residual_id']
        if rid in seen:raise ValueError('Duplicate table review')
        seen.add(rid);r=lookup[rid]
        if decision['source_text_sha256']!=r['source_text_sha256']:raise ValueError('Stale table span')
        pages={p['pdf_page']for p in r['page_evidence']}
        if pages!=set(decision['visually_checked_pdf_pages']):raise ValueError('Incomplete page review')
        heads,data=parse_table(r['source_text']);ch,cd=parse_table(r['candidate_text'])
        if heads!=ch or len(data)!=len(cd):raise ValueError('Editorial structure changed')
        if (len(data),len(heads))!=(decision['data_rows'],decision['columns']):raise ValueError('Table dimensions changed')
        groups=decision.get('row_groups',[[i]for i in range(1,len(data)+1)])
        if sorted(i for group in groups for i in group)!=list(range(1,len(data)+1)):raise ValueError('Incomplete/duplicate row grouping')
        tables.append(dict(table_id=decision['table_id'],source_residual_id=rid,source_unit=r['source_unit'],state=r['state'],
            source_start=r['source_start'],source_end=r['source_end'],source_text=r['source_text'],source_text_sha256=r['source_text_sha256'],
            candidate_text=r['candidate_text'],candidate_text_sha256=r['candidate_text_sha256'],page_evidence=r['page_evidence'],edits=r['edits'],
            column_headers=heads,source_rows=data,candidate_rows=cd,row_groups=groups,
            layout_note_zh=decision['layout_note_zh'],review_kind='same_assistant_visual_table_layout',
            independent_review=False,semantic_truth_assessed=False,natural_corpus_sample=False,translation_gold=False))
    return tables

def build(inventory,review_path,output):
    if output.exists():raise FileExistsError('Immutable table collection')
    review=json.loads(review_path.read_text('utf8'));tables=materialize(inventory,review);output.mkdir(parents=True)
    (output/'tables.jsonl').write_text(''.join(json.dumps(t,ensure_ascii=False)+'\n'for t in tables),'utf8')
    with(output/'cells.tsv').open('w',encoding='utf8',newline='')as stream:
        writer=csv.writer(stream,delimiter='\t');writer.writerow(['table_id','state','data_row','column','column_header','source_cell','candidate_cell','pdf_pages'])
        for t in tables:
            for i,row in enumerate(t['source_rows'],1):
                for j,value in enumerate(row,1):writer.writerow([t['table_id'],t['state'],i,j,t['column_headers'][j-1],value,t['candidate_rows'][i-1][j-1],','.join(str(p['pdf_page'])for p in t['page_evidence'])])
    (output/'README.md').write_text('''# 教材表格补充层

本层由结构清点中的明确审核记录生成，保存原转录/候选文本、行列、空格、页证据和原坐标。是教材理论对比表，不并入编号例组、不当作自然语料频率。单元来源状态沿用，候选没有升级为专家审定。

第三章表1的“动词”是合并表头，本层展开为动词(a)/(b)/(c)，其余三列为词典。三张词典表的加减号含义各依表后说明，不转成统一布尔体偶真值。第十四章表6四个大行各分上下两半，本层为8个序列化数据行，以row_groups明确配对；空单元格保留，不补猜测词形。表5/6的下标是原书义项区分，不是新体标签。

核图只确认所列10表的边界及行列关系；理论主张、词典原始判断和每个词义均未独立验证。逐单元检索仍以知识库来源策略为准；cells.tsv是归档材料，不自动作为RAG或练习池。
''','utf8')
    stats=dict(tables=len(tables),serialized_data_rows=sum(len(t['source_rows'])for t in tables),layout_groups=sum(len(t['row_groups'])for t in tables),
        cells=sum(len(row)for t in tables for row in t['source_rows']),empty_cells=sum(not cell for t in tables for row in t['source_rows']for cell in row),states=dict(Counter(t['state']for t in tables)))
    manifest=dict(schema_version=1,inventory_manifest_sha256=fsh(inventory/'manifest.json'),review_sha256=fsh(review_path),statistics=stats,files={p.name:fsh(p)for p in output.iterdir()if p.is_file()})
    write(output/'manifest.json',manifest);return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inventory',type=Path,default=WORK/'research_exports/aspect_residual_inventory_20261024_001');p.add_argument('--review',type=Path,default=WORK/'reviews/table_layout_review_20261024_001.json');p.add_argument('--output',type=Path,default=WORK/'research_exports/aspect_table_inventory_20261024_001');a=p.parse_args()
    print(json.dumps(build(a.inventory,a.review,a.output)['statistics'],ensure_ascii=False,indent=2))
