"""Append explicit paragraph role decisions without changing source data."""
import argparse,json
from pathlib import Path
from collections import Counter
from build_aspect_example_index import fsh,write
from build_aspect_table_inventory import read_inventory

def materialize(inventory,previous,review):
    _,source=read_inventory(inventory);lookup={r['residual_id']:r for r in source}
    if review['inventory_manifest_sha256']!=fsh(inventory/'manifest.json'):raise ValueError('Inventory version mismatch')
    if review['previous_review_sha256']!=fsh(previous):raise ValueError('Previous review mismatch')
    old=json.loads(previous.read_text('utf8'));rows=list(old['records']);known={r['residual_id']for r in rows}
    for d in review['records']:
        key=d['residual_id']
        if key in known:raise ValueError('Duplicate or overwritten role')
        r=lookup[key]
        if d['source_text_sha256']!=r['source_text_sha256']:raise ValueError('Stale paragraph')
        if not d['paragraph_role']or not d['note_zh']:raise ValueError('Missing explicit role rationale')
        row={k:r[k]for k in ['residual_id','source_unit','source_start','source_end','source_text_sha256','state','page_evidence']}
        row.update(paragraph_role=d['paragraph_role'],selected_supplement_ids=[],all_illustrations_extracted=False,semantic_truth_assessed=False,independent_review=False,review_kind='same_assistant_text_role_review',note_zh=d['note_zh'])
        rows.append(row);known.add(key)
    for unit in review['complete_units_reviewed']:
        expected={r['residual_id']for r in source if r['source_unit']==unit}
        if not expected or not expected<=known:raise ValueError('Incomplete unit role review')
    for row in rows:
        r=lookup[row['residual_id']]
        if any(row[k]!=r[k]for k in ['source_unit','source_start','source_end','source_text_sha256','state','page_evidence']):raise ValueError('Changed historical source binding')
    full=[u for u in sorted({r['source_unit']for r in source})if {r['residual_id']for r in source if r['source_unit']==u}<=known]
    return dict(inventory_manifest_sha256=fsh(inventory/'manifest.json'),previous_review_sha256=fsh(previous),records=rows,
        statistics=dict(role_reviewed_paragraphs=len(rows),unclassified_paragraph_roles=len(source)-len(rows),roles=dict(Counter(r['paragraph_role']for r in rows)),units_with_all_residual_paragraph_roles_reviewed=full),independent_review=False,
        scope_zh='结构角色审核：按已读文本判断论述/词表/句例/公式等，继承原页证据。新记录不声称本批重新逐页核图。角色审核不等于全部行内例已抽取，不裁定理论或翻译真值。')

def build(inventory,previous,review_path,output):
    if output.exists():raise FileExistsError('Immutable cumulative role review')
    review=json.loads(review_path.read_text('utf8'));result=materialize(inventory,previous,review);result['batch_review_sha256']=fsh(review_path);write(output,result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inventory',type=Path,required=True);p.add_argument('--previous',type=Path,required=True);p.add_argument('--review',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(build(a.inventory,a.previous,a.review,a.output)['statistics'],ensure_ascii=False))
