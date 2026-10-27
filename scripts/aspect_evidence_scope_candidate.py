"""Optional local scope experiment; leaves the published RAG rankers unchanged.

This lexical router recognizes some requests for unavailable institutional,
account, current-world or corpus-count evidence. It does not judge whether a
retrieved paragraph semantically entails an answer.
"""
from pathlib import Path
import argparse,json,re
import aspect_candidate_rag as rag

EDITION='aspect_scope_experiment_20261023_001'
QUOTES=re.compile(r'“[^”]*”|「[^」]*」|«[^»]*»|"[^"\n]*"|‘[^’]*’')
NEGATED_ACCESS=re.compile(r'(?:不|不要|无需)(?:查询|读取|获取|访问)[^，。；;!?！？]*')
DOMAINS={
 'zh_institution_or_account':re.compile(r'教室|考场|课表|课程|收费|学费|老师|教师|讲师|手机号|会员|价格|多少钱|成绩|后台|食堂|菜单|学生名单|密码|账号|平台'),
 'ru_institution_or_account':re.compile(r'\b(?:оценк\w*|цен[аыуе]\w*|курс\w*|лекци\w*|препода\w*|парол\w*|аккаунт\w*)\b',re.I),
 'corpus_counts':re.compile(r'语料库|\bнкря\b|\bкорпус\w*\b',re.I),
}
FACTS=re.compile(r'实际|具体|现在|今天|本周|本学期|这学期|我的|某校|某大学|多少钱|收费|手机号|密码|学生名单|后台|查询|帮我下载|\b(?:сегодня|сейчас|мо[йяеёи]\w*|у меня|когда|кто|сколько|цен[аыуе]|парол\w*|202\d)\b',re.I)
COUNT_REQUEST=re.compile(r'(?:具体|实测|本语料库|这个语料库).*(?:多少|例数|比例|次数|频率)|(?:多少|例数|比例|次数|频率).*(?:具体|实测)|\b(?:сколько|дайте число)\b',re.I)
LANGUAGE_TASK=re.compile(r'解释|分析|讨论|讲解|说明|研究时|设计语料库研究|语法形式|语言例子|假想语境|假设的动作|\b(?:объясн\w*|разбер\w*|разгранич\w*|расскаж\w*|исследовании|учебном примере|как отличить)\b',re.I)

def classify(question):
    normalized=question.casefold()
    masked=QUOTES.sub(' [quoted example] ',normalized)
    fact_text=NEGATED_ACCESS.sub('',masked)
    domains=[name for name,pattern in DOMAINS.items()if pattern.search(fact_text)]
    facts=list(dict.fromkeys(m.group(0)for m in FACTS.finditer(fact_text)))
    quantitative=bool('corpus_counts'in domains and COUNT_REQUEST.search(fact_text))
    institutional=any(x!='corpus_counts'for x in domains)and bool(facts)
    outside=bool(institutional or quantitative)
    language=bool(LANGUAGE_TASK.search(masked))
    route='mixed_request'if outside and language else'external_facts_required'if outside else'language_analysis'if language else'unclassified'
    return dict(route=route,matched_domains=domains,matched_fact_cues=facts,quantitative_corpus_request=quantitative,language_task_cue=language,quoted_examples_masked=bool(QUOTES.search(normalized)),classification_kind='transparent_lexical_candidate_not_semantic_judge',limitations_zh='只识别一部分范围外请求，存在漏判和误判；语言分析路由仅允许检索，不承诺材料充分。')

def prepare(question,*,db=None,include_candidates=False,retriever='lexical',max_context_chars=40000):
    assessment=classify(question)
    notice='教材只可支持语言形式与理论说明；没有账号、学校当前记录、价格课表或自然语料统计数据。不得把教材引句当作这些事实的证据。'
    if assessment['route']=='external_facts_required':
        return dict(status='needs_external_evidence',scope_experiment=EDITION,scope=assessment,sources=[],context_characters=0,omitted_sections=[],prompt_package=None,generation_called=False,notice_zh=notice,default_rag_modified=False)
    kwargs=dict(include_candidates=include_candidates,retriever=retriever,max_context_chars=max_context_chars)
    if db is not None:kwargs['db']=db
    result=rag.prepare(question,**kwargs)
    result.update(scope_experiment=EDITION,scope=assessment,generation_called=False,default_rag_modified=False)
    if assessment['route']=='mixed_request':
        result['underlying_retrieval_status']=result['status']
        result['status']='partial_theory_evidence'if result['sources']else'needs_external_evidence'
        result['notice_zh']=notice
        if result.get('prompt_package'):
            result['prompt_package']['system_prompt']=notice+'\n\n'+result['prompt_package']['system_prompt']
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('question');p.add_argument('--classify-only',action='store_true');p.add_argument('--db',type=Path);p.add_argument('--include-candidates',action='store_true');p.add_argument('--retriever',choices=['lexical','passage'],default='lexical');p.add_argument('--max-context-chars',type=int,default=40000);a=p.parse_args()
    result=classify(a.question)if a.classify_only else prepare(a.question,db=a.db,include_candidates=a.include_candidates,retriever=a.retriever,max_context_chars=a.max_context_chars)
    print(json.dumps(result,ensure_ascii=False,indent=2))
