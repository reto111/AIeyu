"""Read-only audit of a pinned aspect candidate and the frozen development cases."""
from pathlib import Path
from contextlib import closing
import argparse,collections,copy,datetime,json
import aspect_candidate_rag as rag
import build_aspect_editorial_candidate as builder

WORK=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference'
def audit(directory,output):
 directory=Path(directory).resolve();output=Path(output)
 if output.exists():raise FileExistsError('Audit reports are immutable')
 db=directory/'aspect_reference.sqlite';source=WORK/'aspect_reference.sqlite'
 source_before=rag.fsh(source);manifest=rag.verify_package(directory)
 if source_before!=manifest['source_db_sha256']:raise ValueError('Foreign source database')
 plan=next(directory.glob('editorial_plan_*.json'));review=next(directory.glob('theory_issue_review_*.json'))
 rebuilt=builder.preview(source,plan,review);sections={s['code']:s for s in rebuilt['sections']}
 compared={};states=collections.Counter();edits=0;accepted=0;forged=0;tampered=0;caution_rejected=0
 allowed={False:set(),True:set()};excluded=[]
 with closing(rag.connect(source))as a,closing(rag.connect(db))as b:
  for name,sql in a.execute("select name,sql from sqlite_master where type='table' order by name"):
   escaped='"'+name.replace('"','""')+'"'
   left=[tuple(x)for x in a.execute('select * from '+escaped)];right=[tuple(x)for x in b.execute('select * from '+escaped)]
   assert sorted(left,key=repr)==sorted(right,key=repr),name
   assert sql==b.execute('select sql from sqlite_master where name=?',(name,)).fetchone()[0]
   compared[name]=len(left)
  assert b.execute('pragma integrity_check').fetchone()[0]=='ok'
  assert not b.execute('pragma foreign_key_check').fetchall()
  for row in b.execute('select * from aspect_candidate_sections order by code'):
   code=row['code'];states[row['state']]+=1;edits+=len(json.loads(row['metadata_json'])['edits'])
   expected=sections[code]
   assert (row['body'],row['title'],row['state'])==(expected['body'],expected['title'],expected['state'])
   assert json.loads(row['metadata_json'])=={k:v for k,v in expected.items()if k not in ('title','body','state')}
   if row['state']=='withheld':
    try:rag.snapshot(b,code,True)
    except ValueError:excluded.append(code)
    else:raise AssertionError('Withheld theory exposure')
    continue
   item=rag.snapshot(b,code,True);allowed[True].add(code)
   if row['state']=='original_source_ready':allowed[False].add(code)
   else:
    try:rag.snapshot(b,code,False)
    except ValueError:pass
    else:raise AssertionError('Candidate exposed by default')
   packet=rag.prepare('指定来源机械引用检查',db=db,code=code,include_candidates=True,max_context_chars=100000)
   assert len(packet['sources'])==1
   response=dict(status='answered',claims=[dict(text_zh='仅检查连续引用，不评价论证语义。',citations=[dict(source_id='A1',quote=item['body'][:30])])])
   assert rag.validate_response(packet,response,db=db)['valid'];accepted+=1
   fake=copy.deepcopy(response);fake['claims'][0]['citations'][0]['quote']='编造的引句，不存在于本节来源正文。'
   try:rag.validate_response(packet,fake,db=db)
   except ValueError:forged+=1
   else:raise AssertionError('Forged quote accepted')
   altered=copy.deepcopy(packet);altered['sources'][0]['body']+='篡改'
   try:rag.validate_response(altered,response,db=db)
   except ValueError:tampered+=1
   else:raise AssertionError('Tampered packet accepted')
   if item['external_source_cautions']:
    removed=copy.deepcopy(packet);removed['sources'][0]['external_source_cautions']=[]
    try:rag.validate_response(removed,response,db=db)
    except ValueError:caution_rejected+=1
    else:raise AssertionError('Removed source caution accepted')
  other=[x[0]for x in b.execute("select code from chunks where code not like 'aspect.ch%'")]
  for code in other:
   try:rag.snapshot(b,code,True)
   except ValueError:pass
   else:raise AssertionError('Non-theory exposure')
 assert dict(states)==manifest['counts'] and edits==manifest['edit_count']
 cases_path=WORK/'rag/question_cases_20261021_001.json';cases=rag.read(cases_path)
 results=[]
 for case in cases['cases']:
  item=dict(**case,modes={})
  for mode,flag in [('original40',False),('candidate'+str(len(allowed[True])),True)]:
   packet=rag.prepare(case['question'],db=db,code=case.get('explicit_code'),include_candidates=flag,max_context_chars=40000)
   included=[s['code']for s in packet['sources']]
   passed=case['expected_source']in included if case.get('expected_source')else packet['status']==case['expected_status']
   current='prepared'if case.get('explicit_code')in allowed[flag]else'no_evidence'
   item['modes'][mode]=dict(status=packet['status'],terms=packet['retrieval']['terms'],ranked_top5=[s['code']for s in packet['retrieval']['ranked_matches']],included_sources=included,omitted_sections=packet['omitted_sections'],expected_source_available=case.get('expected_source')in allowed[flag]if case.get('expected_source')else None,passed=passed,current_scope_expected_status=current if case.get('explicit_code')else None,current_scope_passed=packet['status']==current if case.get('explicit_code')else None)
  results.append(item)
 summary={}
 for mode in results[0]['modes']:
  summary[mode]=dict(natural32_target_in_context=sum(x['modes'][mode]['passed']for x in results[:32]),natural32_targets_available=sum(x['modes'][mode]['expected_source_available']for x in results[:32]),previous8_target_in_context=sum(x['modes'][mode]['passed']for x in results[:8]),explicit_withheld4_rejected=sum(x['modes'][mode]['passed']for x in results[32:36]),unrelated4_no_evidence=sum(x['modes'][mode]['passed']for x in results[36:]))
  summary[mode]['explicit4_current_scope_matched']=sum(x['modes'][mode]['current_scope_passed']for x in results[32:36])
  assert summary[mode]['explicit4_current_scope_matched']==4
 assert rag.fsh(source)==source_before
 assert rag.fsh(Path(rag.__file__))==manifest['files']['aspect_candidate_rag.py']
 report=dict(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_db_sha256=source_before,candidate_manifest_sha256=rag.fsh(directory/'manifest.json'),verified_files=len(manifest['files']),original_tables_compared=compared,counts=dict(states),editorial_edits_replayed=edits,whole_section_quotes_accepted=accepted,forged_quotes_rejected=forged,tampered_packets_rejected=tampered,withheld_theory_rejected=len(excluded),non_theory_rejected=len(other),sqlite_integrity='ok',foreign_key_issues=0,question_cases_sha256=rag.fsh(cases_path),question_case_original_retriever_sha256=cases.get('retriever_sha256'),current_retriever_sha256=rag.fsh(Path(rag.__file__)),development_adjusted=True,question_summary=summary,question_results=results,limitations=['同一助手基于已知来源编写的开发集，已针对其中两题调整检索词形；不是独立留出或泛化召回率。','原40节只对当前可用目标计算覆盖；隔离的预定目标不是检索算法的漏召。','连续引句及篡改拒绝是工程检查，不证明语义；未调用生成API。'])
 report.update(all_theory_units_rebuilt=len(sections),removed_source_cautions_rejected=caution_rejected,explicit_scope_transition_note='旧固定隔离题的预期不改。源节经原著复核后可能成为显式候选；另列按当前真实状态的行为匹配，不能把合法启用误称隔离泄漏。')
 output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
 return {k:v for k,v in report.items()if k not in ('question_results','limitations')}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 print(json.dumps(audit(a.candidate,a.output),ensure_ascii=False,indent=2))
