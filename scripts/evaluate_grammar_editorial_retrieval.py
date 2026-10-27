"""Replay old frozen natural questions against editorial v2 without ranking changes."""
import argparse,json,sqlite3
from pathlib import Path
from grammar_editorial_rag import DEFAULT_DB,prepare,sha,verify_package,thash
from run_grammar_generation_pilot import ROOT,write,now

BASE=ROOT/'data/processed/grammar_reference/rag'
OLD=BASE/'fresh_retrieval_cases_20261016_001.json'
CASES=BASE/'editorial_retrieval_cases_20261022_001.json'
RESULT=BASE/'editorial_retrieval_acceptance_20261022_001.json'
def freeze():
 old=json.loads(OLD.read_text(encoding='utf-8'));cases=[]
 verify_package(DEFAULT_DB.parent)
 with sqlite3.connect(f'file:{DEFAULT_DB.as_posix()}?mode=ro',uri=True) as c:
  for case in old['cases']:
   row={k:case[k] for k in ['case_id','kind','question','expected_codes','forbidden_codes']}
   row['original_kind']=row['kind'];row['source_bindings']=[]
   for code in sorted(set(row['expected_codes']+row['forbidden_codes'])):
    r=c.execute('select title,status,body from chunks where code=?',(code,)).fetchone()
    row['source_bindings'].append({'code':code,'title':r[0],'status':r[1],'body_sha256':thash(r[2])})
   if row['kind']=='quarantine':
    nowready=[s['code'] for s in row['source_bindings'] if s['status']=='ready']
    row['expected_codes']=nowready
    row['forbidden_codes']=[s['code'] for s in row['source_bindings'] if s['status']!='ready']
    row['kind']='newly_available' if nowready else 'quarantine'
   cases.append(row)
 write(CASES,{'frozen_at':now(),'db_sha256':sha(DEFAULT_DB),'previous_cases_sha256':sha(OLD),'implementation_sha256':{n:sha(ROOT/'scripts'/n) for n in ['grammar_editorial_rag.py','grammar_question_search.py']},'limit':3,'max_context_chars':16000,'cases':cases,'limits':'重复使用旧40题，属于版本回归；隔离预期按当前显式状态重新冻结，不是新盲测。'})
 print(json.dumps({'frozen':str(CASES),'cases':len(cases)},ensure_ascii=False))
def run():
 frozen=json.loads(CASES.read_text(encoding='utf-8'))
 assert sha(DEFAULT_DB)==frozen['db_sha256']
 for n,h in frozen['implementation_sha256'].items():assert sha(ROOT/'scripts'/n)==h
 rows=[]
 for case in frozen['cases']:
  packet=prepare(case['question'],limit=frozen['limit'],max_context_chars=frozen['max_context_chars'])
  actual=[s['code'] for s in packet['sources']]
  rows.append({**case,'prepared_codes':actual,'all_expected':bool(case['expected_codes'])and all(x in actual for x in case['expected_codes']),'top1':bool(case['expected_codes'])and actual[:1]==case['expected_codes'],'forbidden_leaks':sorted(set(actual)&set(case['forbidden_codes'])),'empty':not actual,'packet':packet})
 summary={}
 for kind in sorted(set(r['kind'] for r in rows)):
  rr=[r for r in rows if r['kind']==kind]
  summary[kind]={'total':len(rr),'all_expected':sum(r['all_expected'] for r in rr),'top1':sum(r['top1'] for r in rr),'empty':sum(r['empty'] for r in rr),'no_forbidden_leak':sum(not r['forbidden_leaks'] for r in rr)}
 assert sha(DEFAULT_DB)==frozen['db_sha256']
 write(RESULT,{'evaluated_at':now(),'cases_sha256':sha(CASES),'database_sha256':sha(DEFAULT_DB),'summary':summary,'records':rows,'external_api_calls':0,'ranking_changed':False,'limits':frozen['limits']})
 print(json.dumps({'artifact':str(RESULT),'summary':summary,'misses':[{k:r[k]for k in ['case_id','question','expected_codes','prepared_codes']}for r in rows if r['expected_codes']and not r['all_expected']]},ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','run']);a=p.parse_args()
 freeze() if a.action=='freeze' else run()
