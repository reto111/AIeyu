"""Replay frozen pilot evidence and record assistant semantic review separately."""
import json, statistics
from pathlib import Path
from run_grammar_generation_pilot import OUT, ROOT, DEFAULT_DB, digest, write, now
from grammar_editorial_rag import verify_package, validate_response
from grammar_reference import strip_search_formatting

# Ordered by the rubric items frozen before generation. These are source-relative
# assistant judgments, not an independent expert's blind annotations.
SCORES={
 'P01':([1,1],[1,1],'对照核心正确；扩展例леди属表人，与题问非动物范围不同。'),
 'P02':([1,1,1],[0,0,1],'对照合理拒绝冒称本书表述，同时给出一般知识；未覆盖书内历史叙述，不按语法错误处理。'),
 'P03':([1,1],[0,0],'对照把第二格误归为原形，虽正确列出三五六格，仍不满足两条完整规则。'),
 'P04':([1,1,1],[0,0,1],'对照列出的间接格字母形式正确，但又混同软硬词尾并误称дво́их、тро́их词干重音。'),
 'P05':([1,1,1],[1,1,1],'两组核心均覆盖；RAG引用可逐字定位。'),
 'P06':([1,1,1],[0,0,1],'对照称词干以*k结尾又举*berg-ti，误述由*k到г，并把阳性词干г当形式词尾；过去时不分人称、分性数覆盖。'),
 'P07':([1,1,1],[1,1,0],'对照覆盖基本区别和未完成体表不可能，但未覆盖冻结要求的反问语境；泛称完成体可禁止不代替该具体说明。'),
 'P08':([1,1,1],[1,0,0],'对照正确拒绝一律完成体，但漏可能性并误称стоит后通常未完成体，随即承认заговорить完成体，自相矛盾。'),
 'P09':([1,1],[1,1],'两组依附关系均正确；RAG有引文重音和Markdown逐字格式问题。'),
 'P10':([1,1],[1,1],'两组均拒绝编造统计；RAG检索返回相关语法而非统计依据，拒答成功不等于检索器识别范围外。')
}

def main():
 manifest=json.loads((OUT/'freeze_manifest.json').read_text(encoding='utf-8'))
 for rel,h in manifest['files'].items():
  if digest(OUT/rel)!=h:raise ValueError('Frozen input changed: '+rel)
 protocol=json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
 assert digest(DEFAULT_DB)==protocol['db_sha256']
 verify_package(DEFAULT_DB.parent)
 records=[];all_citations=[]
 for case in protocol['cases']:
  cid=case['id'];packet=json.loads((OUT/'packets'/f'{cid}.json').read_text(encoding='utf-8'))
  actual=[s['code'] for s in packet['sources']]
  for group in ['rag','control']:
   paths=list((OUT/'requests').glob(f'*_{cid}_{group}.json'));assert len(paths)==1
   req=paths[0];request=json.loads(req.read_text(encoding='utf-8'))
   prompt=json.loads(request['messages'][1]['content'])
   assert request['messages'][0]['content']==protocol['system_prompt']
   assert prompt=={'question':case['question'],'retrieved_sources':packet['sources'] if group=='rag' else []}
   response_path=OUT/'responses'/req.name
   response=json.loads(response_path.read_text(encoding='utf-8'))
   assert (OUT/'attempts'/req.name).exists()
   assert 'error'not in response and response['finish_reason']=='stop'
   answer=response['parsed'];points=SCORES[cid][0 if group=='rag' else 1]
   assert len(points)==len(case['rubric'])
   validation=None
   if group=='rag':
    try:validation=validate_response(packet,answer)
    except Exception as e:validation={'valid':False,'reason':str(e),'semantic_correctness_assessed':False}
   sources={s['source_id']:s for s in packet['sources']}
   citations=[]
   for k,claim in enumerate(answer.get('claims',[]),1):
    for j,c in enumerate(claim.get('citations',[]),1):
     source=sources.get(c['source_id']) if group=='rag' else None
     q=c['quote'];exact=bool(source and q in strip_search_formatting(source['body']))
     minimum=len(''.join(q.split()))>=6
     item={'request_id':req.stem,'claim':k,'citation':j,'source_id':c['source_id'],'quote':q,'exact_in_normalized_source':exact,'minimum_six_nonspace':minimum,'passes_frozen_quote_rule':exact and minimum}
     citations.append(item);all_citations.append(item)
   records.append({'case_id':cid,'group':group,'request_id':req.stem,'response_sha256':digest(response_path),'rubric':case['rubric'],'rubric_points':points,'points':sum(points),'possible':len(points),'review_note':SCORES[cid][2],'response_status':answer['status'],'mechanical_validation':validation,'citations':citations,'expected_codes':case['expected_codes'],'prepared_codes':actual,'all_expected_retrieved':all(c in actual for c in case['expected_codes']) if case['expected_codes'] else None,'elapsed_seconds':response['elapsed_seconds'],'usage':response['raw_response']['usage'],'returned_model':response['raw_response'].get('model')})
 groups={}
 for group in ['rag','control']:
  rows=[r for r in records if r['group']==group]
  groups[group]={'responses':len(rows),'rubric_points':sum(r['points'] for r in rows),'rubric_possible':sum(r['possible'] for r in rows),'fully_covered_cases':sum(r['points']==r['possible'] for r in rows),'prompt_tokens':sum(r['usage']['prompt_tokens'] for r in rows),'completion_tokens':sum(r['usage']['completion_tokens'] for r in rows),'median_latency_seconds':statistics.median(r['elapsed_seconds'] for r in rows),'sum_request_seconds':round(sum(r['elapsed_seconds'] for r in rows),3),'answered':sum(r['response_status']=='answered' for r in rows),'insufficient':sum(r['response_status']=='insufficient_evidence' for r in rows)}
 groups['rag']['mechanically_valid_all']=sum(r['mechanical_validation']['valid'] for r in records if r['group']=='rag')
 groups['rag']['mechanically_valid_answered']=sum(r['mechanical_validation']['valid'] for r in records if r['group']=='rag'and r['response_status']=='answered')
 report={'audited_at':now(),'protocol_sha256':digest(OUT/'protocol.json'),'frozen_manifest_sha256':digest(OUT/'freeze_manifest.json'),'attempts':len(list((OUT/'attempts').glob('*.json'))),'successful_responses':len(records),'max_attempts':20,'groups':groups,'citation_summary':{'total':len(all_citations),'exact_in_normalized_source':sum(c['exact_in_normalized_source'] for c in all_citations),'passes_frozen_quote_rule':sum(c['passes_frozen_quote_rule'] for c in all_citations)},'records':records,'semantic_review_limits':['同一助手制定题目并据源评分；不是专家独立盲评。','样本10题为开发性演示，不能推断总体正确率或RAG因果效果。','P02是本书表述题，对照合理拒答；分数衡量任务覆盖，不能把拒答叫语法错误。','P04及P06题干各带一个拉丁e，冻结后未改；检索仍命中，不能据此宣称通用OCR鲁棒性。','本书及编校版是评分依据，不代表全部现代规范；集合数词第四格表述简化需独立专家评议。','逐字引用存在不等于引句充分支持整条主张；另见人工阅读的引文语义说明。'],'source_database_unchanged':digest(DEFAULT_DB)==protocol['db_sha256'],'new_api_calls_in_audit':0}
 write(OUT/'audit_001.json',report)
 print(json.dumps({k:report[k] for k in ['attempts','successful_responses','groups','citation_summary']},ensure_ascii=False))
if __name__=='__main__':main()
