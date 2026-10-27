"""Describe remaining Russian-bearing spans; never infer that they are examples."""
import argparse,json,re,hashlib
from collections import Counter
from pathlib import Path
from aspect_material_roles import read_collection

PRIORITY_ROLES={'exposition_with_sentence_illustrations','exposition_with_accepted_and_unacceptable_illustrations','exposition_with_reformulations','exposition_with_phrase_illustrations','unacceptability_phrase_illustrations','unacceptability_sentence_illustrations','standalone_comparison_group','exposition_with_unacceptable_illustrations','exposition_with_lexical_and_sentence_illustrations','exposition_with_accepted_and_questionable_illustrations'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build(roles,examples):
    rm,paragraphs=read_collection(roles);em=json.loads((examples/'manifest.json').read_text('utf8'))
    if rm['examples_manifest_sha256']!=sha(examples/'manifest.json'):raise ValueError('Role links and examples use different editions')
    for path,h in em['files'].items():
        if sha(examples/path)!=h:raise ValueError('Changed examples')
    rows=list(map(json.loads,(examples/'examples.jsonl').read_text('utf8').splitlines()));by_residual={r['residual_id']:[]for r in paragraphs}
    for r in rows:by_residual[r['source_residual_id']].append(r)
    result=[]
    for p in paragraphs:
        linked=sorted(by_residual[p['residual_id']],key=lambda r:r['source_start']);assert {r['example_id']for r in linked}==set(p['extracted_illustration_ids'])
        cursor=p['source_start'];gaps=[]
        for r in linked:
            a,b=r['source_start'],r['source_end'];assert cursor<=a<b<=p['source_end'];assert p['source_text'][a-p['source_start']:b-p['source_start']]==r['source_text']
            gaps.append((cursor,a));cursor=b
        gaps.append((cursor,p['source_end']));segments=[]
        for a,b in gaps:
            text=p['source_text'][a-p['source_start']:b-p['source_start']]
            count=len(re.findall('[А-Яа-яЁё]',text))
            if count:segments.append(dict(source_start=a,source_end=b,cyrillic_letters=count,text=text))
        priority=p['paragraph_role']in PRIORITY_ROLES and bool(segments)and p['state']!='withheld'
        result.append(dict(residual_id=p['residual_id'],source_unit=p['source_unit'],state=p['state'],paragraph_role=p['paragraph_role'],source_start=p['source_start'],source_end=p['source_end'],page_evidence=p['page_evidence'],linked_example_ids=[r['example_id']for r in linked],uncovered_cyrillic_letters=sum(r['cyrillic_letters']for r in segments),uncovered_russian_bearing_segments=segments,priority_role_queue=priority,all_inline_illustrations_extracted=False,remaining_example_count=None))
    return dict(schema_version=1,role_manifest_sha256=sha(roles/'manifest.json'),example_manifest_sha256=sha(examples/'manifest.json'),statistics=dict(paragraphs=len(result),linked_example_occurrences=len(rows),paragraphs_with_links=sum(bool(r['linked_example_ids'])for r in result),paragraphs_with_uncovered_cyrillic=sum(bool(r['uncovered_cyrillic_letters'])for r in result),priority_role_paragraphs=sum(r['priority_role_queue']for r in result),priority_with_existing_links=sum(r['priority_role_queue']and bool(r['linked_example_ids'])for r in result),states=dict(Counter(r['state']for r in result))),priority_role_definitions=sorted(PRIORITY_ROLES),remaining_example_count=None,automatically_added_examples=0,independent_review=False,interpretation_zh='每段已圈定例证区间之外仍有俄文字母的原转录范围；可能只是术语、词汇列举、回指或作者分析，不等于未抽取例数。优先队列只依既有材料角色，不自动判定新例证。全部段落的行内抽取完成状态仍未知；有链接也不表示该段已穷尽。隔离段只清点、不进入优先可用队列。',paragraphs=result)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--roles',type=Path,required=True);p.add_argument('--examples',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError('Immutable queue snapshot')
    d=build(a.roles,a.examples);a.output.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(d['statistics'],ensure_ascii=False))
