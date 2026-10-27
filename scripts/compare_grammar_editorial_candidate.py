"""One-shot local comparison on preserved development and pre-frozen new cases."""
import json
from grammar_editorial_rag import prepare,DEFAULT_DB,sha
from grammar_editorial_search_candidate import prepare as candidate_prepare
from run_grammar_generation_pilot import ROOT,write,now

BASE=ROOT/'data/processed/grammar_reference/rag'
def main():
 newpath=BASE/'editorial_candidate_newcases_20261022_001.json'
 oldpath=BASE/'editorial_retrieval_cases_20261022_001.json'
 new=json.loads(newpath.read_text(encoding='utf-8'));old=json.loads(oldpath.read_text(encoding='utf-8'))
 assert sha(DEFAULT_DB)==new['database_sha256']==old['db_sha256']
 assert sha(ROOT/'scripts/grammar_question_search.py')==new['baseline_sha256']
 records=[]
 for split,data in [('development40',old['cases']),('new20',new['cases'])]:
  for case in data:
   q=case['question'];expected=case['expected_codes'];baseline=prepare(q);candidate=candidate_prepare(q)
   row={'split':split,'id':case.get('id',case.get('case_id')),'question':q,'expected_codes':expected,'kind':case.get('kind','positive'if expected else'negative'),'expansions':candidate['candidate_query_expansions']}
   for name,p in [('baseline',baseline),('candidate',candidate)]:
    actual=[s['code'] for s in p['sources']]
    row[name]={'codes':actual,'all_expected':all(c in actual for c in expected)if expected else None,'top1':actual[:1]==expected if len(expected)==1 else None,'empty':not actual,'packet':p}
   records.append(row)
 summary={}
 for split in ['development40','new20']:
  rr=[r for r in records if r['split']==split];positive=[r for r in rr if r['expected_codes']];negative=[r for r in rr if r['kind']=='negative']
  summary[split]={'positive_cases':len(positive),'negative_cases':len(negative)}
  for name in ['baseline','candidate']:
   summary[split][name]={'all_targets':sum(r[name]['all_expected']for r in positive),'negative_empty':sum(r[name]['empty']for r in negative)}
  summary[split]['regressions']=[r['id']for r in positive if r['baseline']['all_expected']and not r['candidate']['all_expected']]
  summary[split]['improvements']=[r['id']for r in positive if not r['baseline']['all_expected']and r['candidate']['all_expected']]
 write(BASE/'editorial_candidate_comparison_20261022_001.json',{'evaluated_at':now(),'source_sha256':sha(DEFAULT_DB),'frozen_newcases_sha256':sha(newpath),'candidate_sha256':sha(ROOT/'scripts/grammar_editorial_search_candidate.py'),'summary':summary,'records':records,'api_calls':0,'ranking_default_changed':False,'limits':'新题为同一助手针对开发缺口编写，未据结果调参；不是独立专家题集。'})
 print(json.dumps({'summary':summary,'new_misses':[{k:r[k]for k in ['id','question','expected_codes','expansions']}|{'actual':r['candidate']['codes']}for r in records if r['split']=='new20'and r['expected_codes']and not r['candidate']['all_expected']]},ensure_ascii=False))
if __name__=='__main__':main()
