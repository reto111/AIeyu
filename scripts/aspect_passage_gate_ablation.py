"""Diagnostic removal of one topic gate, isolated from the default retriever."""
from pathlib import Path
from contextlib import closing
from collections import Counter
import argparse,ast,copy,datetime,inspect,json
import aspect_candidate_rag as rag

WORK=Path(__file__).resolve().parents[1]/'data/processed/aspect_reference'
CANDIDATE=WORK/'research_exports/aspect_editorial_candidate_20261023_002'
CASES=WORK/'rag/extended_question_cases_20261022_001.json'
GATE="if not set(terms)-{'俄语','汉语','动词','结果','语法意义'}:return [],terms"

def isolated_ablation():
    tree=ast.parse(inspect.getsource(rag.search_question_passages))
    function=tree.body[0];expected=ast.parse(GATE).body[0]
    gates=[i for i,node in enumerate(function.body)if ast.dump(node,include_attributes=False)==ast.dump(expected,include_attributes=False)]
    if gates!=[2]:raise ValueError('Source gate changed; cannot claim a one-gate ablation')
    original=copy.deepcopy(function);del function.body[gates[0]]
    if ast.dump(original.body.pop(2),include_attributes=False)!=ast.dump(expected,include_attributes=False):raise ValueError('Unexpected transformation')
    if ast.dump(original,include_attributes=False)!=ast.dump(function,include_attributes=False):raise ValueError('Additional ranking change')
    namespace=dict(vars(rag));exec(compile(ast.fix_missing_locations(tree),'<isolated_topic_gate_ablation>','exec'),namespace)
    # Rebind only this function's globals, preserving the original preparer AST.
    preparer=ast.parse(inspect.getsource(rag.prepare));exec(compile(preparer,'<unchanged_preparer>','exec'),namespace)
    return namespace['prepare'],dict(original_function_sha256=rag.tsh(inspect.getsource(rag.search_question_passages)),ablated_function_ast_sha256=rag.tsh(ast.dump(function,include_attributes=False)),unchanged_preparer_ast_sha256=rag.tsh(ast.dump(preparer,include_attributes=False)),removed_gate=GATE)

def run(output):
    output=Path(output);protocol_path=output.with_name(output.stem+'_protocol.json')
    if output.exists()or protocol_path.exists():raise FileExistsError('Ablation evidence is immutable')
    rag.verify_package(CANDIDATE);source_pin=rag.fsh(Path(rag.__file__));candidate_pin=rag.fsh(CANDIDATE/'manifest.json');case_pin=rag.fsh(CASES)
    protocol=dict(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate_manifest_sha256=candidate_pin,retriever_sha256=source_pin,case_file_sha256=case_pin,scope='既有已知50题的诊断消融，不是独立留出；因已观察漏检而选择该门槛。',intervention=GATE,changed_component='remove_only_this_early_return',constant_components=['query features','weights','passage windows','rank fusion','top5','whole-section context budget40000','source states','quote validation'],variants=['baseline_passage','without_topic_gate'],source_scopes=['original40','candidate93'],default_retriever_changed=False,generation_called=False,success_measures=['target_in_prepared_sources_on_natural24','no_evidence_on_overlap8_and_unrelated8','current_source_scope_matching_on_explicit10'],not_a_parameter_search=True)
    protocol_path.write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n','utf8')
    prepare,transformation=isolated_ablation();case_data=rag.read(CASES);records=[];gate_closed=Counter();unchanged_when_gate_open=0
    for case in case_data['cases']:
        item=dict(case=case,variants={})
        for flag in (False,True):
            scope='candidate93'if flag else'original40';packets={}
            for name,fn in [('baseline_passage',rag.prepare),('without_topic_gate',prepare)]:
                p=fn(case['question'],db=CANDIDATE/'aspect_reference.sqlite',code=case.get('explicit_code'),include_candidates=flag,max_context_chars=40000,retriever='passage')
                included=[s['code']for s in p['sources']];target=case.get('expected_source')
                item['variants'][scope+'_'+name]=dict(status=p['status'],included_sources=included,omitted_sections=p['omitted_sections'],context_characters=p['context_characters'],target_in_sources=target in included if target else None,initial_expected_status_matched=p['status']==case.get('expected_status')if not target else None)
                packets[name]=p
                if p['sources']:
                    response=dict(status='answered',claims=[dict(text_zh='仅检验引用及来源范围',citations=[dict(source_id=s['source_id'],quote=s['body'])for s in p['sources']])]);rag.validate_response(p,response,db=CANDIDATE/'aspect_reference.sqlite')
            if case.get('explicit_code')or set(rag.passage_terms(case['question']))-{'俄语','汉语','动词','结果','语法意义'}:
                if packets['baseline_passage']!=packets['without_topic_gate']:raise ValueError('A change occurred while the gate was open or bypassed explicitly')
                unchanged_when_gate_open+=1
            else:gate_closed[scope]+=1
        records.append(item)
    with closing(rag.connect(CANDIDATE/'aspect_reference.sqlite'))as c:states={r['code']:r['state']for r in c.execute('select code,state from aspect_candidate_sections')}
    summaries={}
    for variant in records[0]['variants']:
        summary={}
        for kind in dict.fromkeys(x['case']['kind']for x in records):
            group=[x for x in records if x['case']['kind']==kind]
            score=sum(x['variants'][variant]['target_in_sources']if x['case'].get('expected_source')else x['variants'][variant]['status']=='no_evidence'for x in group)
            summary[kind]=dict(total=len(group),target_covered_or_no_evidence=score)
            if kind=='current_withheld_explicit':
                flag=variant.startswith('candidate93');summary[kind]['current_scope_matched']=sum((x['variants'][variant]['status']=='prepared')==(states.get(x['case']['explicit_code'])=='original_source_ready'or(flag and states.get(x['case']['explicit_code'])=='model_editorial_candidate'))for x in group)
        summaries[variant]=summary
    if source_pin!=rag.fsh(Path(rag.__file__))or candidate_pin!=rag.fsh(CANDIDATE/'manifest.json')or case_pin!=rag.fsh(CASES):raise ValueError('A frozen input changed')
    result=dict(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),protocol_sha256=rag.fsh(protocol_path),script_sha256=rag.fsh(Path(__file__)),transformation=transformation,summary=summaries,records=records,gate_closed_cases_by_scope=dict(gate_closed),unchanged_packets_when_gate_open_or_explicit=unchanged_when_gate_open,original_retriever_file_unchanged=True,candidate_and_cases_unchanged=True,default_changed=False,generation_called=False,independent_semantic_review=False,limitations=['只量化已知开发题上的单门槛效应，不是独立召回率或答案正确率。','引文逐字存在与来源隔离通过，不等于证据语义充分。','原旧隔离预期与当前合法范围同时报告，不把合法启用误称泄漏。','移除主题词门槛可能增加范围外证据，不能据自然题改善直接默认化。'])
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    return dict(summary=summaries,gate_closed_cases_by_scope=dict(gate_closed),unchanged_packets=unchanged_when_gate_open,default_changed=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();print(json.dumps(run(args.output),ensure_ascii=False,indent=2))
