"""Optional book-evidence requirement guard; fixed lexical rules, no network or generation."""
from __future__ import annotations
import argparse,copy,hashlib,json,re
from pathlib import Path
import tonglun_rag as rag
import tonglun_question_rag_candidate as retrieval

VERSION='tonglun.requirements_candidate.20261025.001'
def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')).hexdigest()

def assess(question):
    if not isinstance(question,str)or not 1<=len(question.strip())<=2000:raise ValueError('Invalid question')
    q=question.strip();reasons=[]
    def add(code,required):reasons.append(dict(code=code,required_evidence=required,available_from_this_book_alone=False))
    numerical=re.search(r'频次|出现(?:过)?多少次|出现次数|发生多少|多少回|年度频|所占比例|占比|百分之几',q)
    external=re.search(r'网络|微博|新闻|语料库|现代口语|真实对话|对话资料|百万|过去十年',q)
    if numerical and external:add('external_corpus_measurement','specified external corpus, sampling period, counting method and measured results')
    personal=re.search(r'真实掌握率|(?:学生|考生|我).{0,45}(?:掌握率|全国.{0,10}(?:第几|排名)|能力.{0,10}(?:排名|第几))',q)
    if personal:add('individual_learning_measurement','actual named student responses or validated assessment data; no student database read by this tool')
    if re.search(r'今天|现在|目前',q)and re.search(r'商店|网店|售价|价格|便宜',q):add('current_market_information','current seller and price evidence')
    if re.search(r'20\d{2}',q)and re.search(r'报名|考试',q)and re.search(r'日期|截止|时间',q):add('exam_schedule_information','dated official examination announcement')
    if re.search(r'曲线|示意图|音高图|这段语音|原录音|原始录音',q)and re.search(r'Hz|赫兹|毫秒|F0|F₀|基频数值',q,re.I)and re.search(r'读出|测出|测量出|给出|恢复|还原|算出|计算出|是多少|毫秒数',q):add('unavailable_acoustic_measurement','original audio or calibrated acoustic measurements; schematic images do not supply these numbers')
    if '余弦相似度'in q and re.search(r'这次|本次|本轮',q)and re.search(r'多少|分数|具体',q):add('uncomputed_retrieval_metric','actual cosine score; current lexical candidate does not compute cosine similarity')
    return dict(version=VERSION,question_sha256=hashlib.sha256(q.encode('utf8')).hexdigest(),reasons=reasons,requirement_blocked=bool(reasons),unrecognized_requirements_may_remain=True,adequacy_confirmed=False)

def canonical_prompt(packet):
    return dict(system_prompt=rag.SYSTEM_PROMPT,user_payload=dict(question=packet['question'],retrieved_sources=packet['sources']))if packet['sources']else None

def check_base(packet):
    if not isinstance(packet,dict)or packet.get('schema_version')!=1 or packet.get('status')not in('prepared','no_evidence','context_over_budget'):raise ValueError('Invalid base packet')
    if packet['question']!=packet['question'].strip()or packet['prompt_package']!=canonical_prompt(packet):raise ValueError('Question/source/system prompt mismatch')
    if bool(packet['sources'])!=(packet['status']=='prepared'):raise ValueError('Source/status mismatch')
    if packet['sources']:rag.validate(packet,dict(status='insufficient_evidence',message_zh='本地来源重放检查'))

def guard(packet):
    check_base(packet);decision=assess(packet['question']);out=copy.deepcopy(packet)
    if decision['requirement_blocked']:out.update(status='unsupported_evidence_requirement',prompt_package=None)
    out['requirements_guard']=dict(**decision,original_status=packet['status'],original_packet_sha256=digest(packet),outbound_prompt_allowed=bool(out['prompt_package']))
    return out

def validate_guarded(packet):
    if not isinstance(packet,dict)or'requirements_guard'not in packet:raise ValueError('Guard metadata missing')
    meta=packet['requirements_guard'];decision=assess(packet['question'])
    for key,value in decision.items():
        if meta.get(key)!=value:raise ValueError('Requirement assessment changed')
    base=copy.deepcopy(packet);base.pop('requirements_guard');base['status']=meta['original_status'];base['prompt_package']=canonical_prompt(base)
    check_base(base)
    if digest(base)!=meta['original_packet_sha256']:raise ValueError('Original evidence packet changed')
    expected=guard(base)
    if expected!=packet:raise ValueError('Guarded prompt/status changed')
    return dict(status='requirements_packet_checked',requirement_blocked=decision['requirement_blocked'],outbound_prompt_allowed=meta['outbound_prompt_allowed'],source_count=len(packet['sources']),adequacy_confirmed=False,limits='规则和来源/提示词重放；未识别不等于证据充分，未验证生成回答。')

def prepare(question,limit=3,max_context_chars=16000):return guard(retrieval.prepare(question,limit,max_context_chars))

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--question',required=True);ap.add_argument('--limit',type=int,default=3);ap.add_argument('--max-context-chars',type=int,default=16000);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    packet=prepare(a.question,a.limit,a.max_context_chars);validate_guarded(packet)
    with a.output.open('x',encoding='utf8')as f:json.dump(packet,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(status=packet['status'],requirement_blocked=packet['requirements_guard']['requirement_blocked'],outbound_prompt_allowed=packet['requirements_guard']['outbound_prompt_allowed'],source_count=len(packet['sources']),output=str(a.output)),ensure_ascii=False))
