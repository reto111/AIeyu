"""Bind targeted supplementary evidence without rewriting model study cards."""
from pathlib import Path
from contextlib import closing
from collections import Counter
import argparse,json
import aspect_candidate_rag as rag
import aspect_study_cards as cards
import build_aspect_example_index as evidence
from build_aspect_annotation_pilot_v2 import bind_span

def prepare(input_path,collection,candidate):
    data=rag.read(input_path);m,items=cards.verify(collection);rag.verify_package(candidate)
    if data['collection_manifest_sha256']!=cards.sha(collection/'manifest.json')or data['candidate_manifest_sha256']!=rag.fsh(candidate/'manifest.json'):raise ValueError('Support edition mismatch')
    by_code={x['code']:x for x in items};seen=set();records=[]
    with closing(rag.connect(candidate/'aspect_reference.sqlite'))as c:
        for item in data['targeted_support_cases']:
            code=item['code'];n=item['claim_index'];key=(code,n)
            if key in seen:raise ValueError('Repeated support claim')
            seen.add(key);card=by_code[code]
            if type(n)is not int or not 1<=n<=len(card['claims']):raise ValueError('Invalid claim index')
            claim=card['claims'][n-1]
            if item['claim_text_sha256']!=rag.tsh(claim['text_zh'])or item['original_quote_sha256']!=claim['quote_sha256']:raise ValueError('Original model claim or quote changed')
            raw=c.execute('select * from chunks where code=?',(code,)).fetchone();current=c.execute('select * from aspect_candidate_sections where code=?',(code,)).fetchone();spans=evidence.bindings(c,raw)
            if card['state']!=current['state']or card['source_body_sha256']!=rag.tsh(raw['body']):raise ValueError('Source status changed')
            supplements=[]
            if not item['supplementary_quotes']:raise ValueError('Empty supplement')
            for q in item['supplementary_quotes']:
                if not q['supports_zh']or current['body'].count(q['quote'])!=1:raise ValueError('Supplement changed or ambiguous')
                supplements.append(dict(supports_zh=q['supports_zh'],**bind_span(raw,spans,q['quote'])))
            records.append(dict(code=code,claim_index=n,model_claim=claim['text_zh'],claim_text_sha256=item['claim_text_sha256'],original_quote=claim['quote'],original_quote_sha256=claim['quote_sha256'],source_state=current['state'],eligible_original=current['state']=='original_source_ready',eligible_with_candidates=current['state']in {'original_source_ready','model_editorial_candidate'},source_unit_sha256=rag.tsh(raw['body']),candidate_unit_sha256=rag.tsh(current['body']),single_quote_model_assessment=item['single_quote_model_assessment'],reason_zh=item['reason_zh'],supplementary_evidence=supplements,external_source_cautions=card['external_source_cautions'],independent_entailment_assessment=False,model_claim_text_changed=False,source_isolation_lifted=False))
    return dict(schema_version=1,created_at=data['created_at'],input_sha256=rag.fsh(input_path),collection_manifest_sha256=cards.sha(collection/'manifest.json'),candidate_manifest_sha256=rag.fsh(candidate/'manifest.json'),builder_sha256=rag.fsh(Path(__file__)),model_review_read_pairs=data['model_review_read_pairs'],read_scope=data['read_scope'],targeted_claim_count=len(records),supplementary_quote_count=sum(len(x['supplementary_evidence'])for x in records),source_states=dict(Counter(x['source_state']for x in records)),records=records,independent_semantic_review=False,rag_integration=False,training_pool_import=False,limitations=['350是本轮主张/引句配对阅读覆盖，不代表重新完整阅读100节或独立正确率。','12项为有意选择的证据覆盖样例，不是全体问题数、随机样本或充分性比例。','41段补充引句只证明相应原书位置存在；多引句仍不自动保证模型解释及所有推理正确。','两条源节隔离样例仅归档，补充引句不解除任何来源隔离；旧学习卡不改写。'])

def write(input_path,collection,candidate,output):
    if output.exists()or output.with_suffix('.md').exists():raise FileExistsError('Immutable support overlay')
    result=prepare(input_path,collection,candidate)
    lines=['# 学习卡补充证据：12项定向样例','','同一助手完成350条主张/引句配对阅读后，定向补充12项41段原书引句。不是350项充分性认证；隔离源节只归档，旧卡片不变。','','|源节/主张|状态|旧引句覆盖问题|补充引句数|','|---|---|---|---|']
    for x in result['records']:lines.append(f"|{x['code']} / {x['claim_index']}|{x['source_state']}|{x['reason_zh']}|{len(x['supplementary_evidence'])}|")
    for x in result['records']:
        lines+=['',f"## {x['code']}：主张{x['claim_index']}",'',x['model_claim'],'',x['reason_zh'],'']
        for q in x['supplementary_evidence']:
            pages=', '.join(str(p['pdf_page'])+'/'+str(p['printed_page'])for p in q['page_evidence'])
            lines.append(f"- {q['supports_zh']}（PDF/印刷{pages}）：{q['text']}")
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');output.with_suffix('.md').write_text('\n'.join(lines)+'\n','utf8');return {k:v for k,v in result.items()if k not in ('records','limitations')}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('input','collection','candidate','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(write(a.input,a.collection,a.candidate,a.output),ensure_ascii=False,indent=2))
