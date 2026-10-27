"""Optional local scope and evidence checks for the frozen editorial edition.

No generation/network/database writes. This layer does not certify semantics.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

import grammar_editorial_rag as base
from grammar_reference import strip_search_formatting

GUARD_VERSION = 1
POLICY = '''每条主张都须有连续逐字引用，不得添加无引用的一般知识补充；最多10条主张。
引用中去除Markdown加粗符号，保留俄语重音及ё，至少6个非空白字符。
不得以相关章节代替不存在的统计或个人数据；材料不足应明确返回insufficient_evidence。
只输出前述JSON结构，不增加其他字段。'''

def canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError('Expected a finite JSON value') from exc

def check_question(question):
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 2000:
        raise ValueError('Question must contain 1–2000 characters')

def assess_scope(question):
    """Finite request-capability rules; allow is not a sufficiency judgment."""
    check_question(question)
    q = question.lower()
    reasons = []
    if re.search(r'国家语料库|нкря|russian national corpus', q) and re.search(
            r'频率|频次|次数|多少次|统计|检索.{0,6}(?:日期|时间)', q):
        reasons.append('external_corpus_measurement')
    if re.search(r'(?:我|个人|账号).{0,14}(?:考试记录|学习历史|学习记录|考试历史|成绩)', q) and re.search(
            r'正确率|错误率|掌握|百分|判断|计算', q):
        reasons.append('private_learning_record_measurement')
    if re.search(r'录音|音频|mp3', q) and re.search(r'下载|链接|地址', q):
        reasons.append('external_audio_artifact')
    if re.search(r'查重率|查重报告', q):
        reasons.append('external_plagiarism_report')
    language_use = bool(re.search(r'怎么说|如何表达|怎样表达|怎样变格|如何变格|表达价格|数词.{0,8}表达', q))
    if not language_use and re.search(r'多少钱|收费|费用|每小时', q) and re.search(
            r'出版社|排版|排印|制作|临时工|每小时', q):
        reasons.append('external_service_cost')
    if re.search(r'全书|整本书|所有.{0,12}逐页|哪一页|在哪一页', q) and re.search(
            r'频次|频率|出现次数|次数最多|排名|精确频次', q):
        reasons.append('whole_book_aggregation_not_provided')
    return {'decision': 'unsupported_request' if reasons else 'allow',
            'reasons': reasons,
            'limits': '有限请求范围规则；allow不保证检索完整、材料充分或回答正确。'}

def verified_database(db):
    db = Path(db).resolve()
    manifest = base.verify_package(db.parent)
    if db.name != 'grammar_reference.sqlite' or manifest['files'].get(db.name) != base.sha(db):
        raise ValueError('Database must be the manifest-bound editorial database')
    return db, manifest

def prepare(question, *, db=base.DEFAULT_DB, retriever='baseline', code=None,
            query=None, limit=3, max_context_chars=16000):
    check_question(question)
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ValueError('Invalid evidence limit')
    if type(max_context_chars) is not int or not 1 <= max_context_chars <= 160000:
        raise ValueError('Invalid context budget')
    if retriever not in ('baseline', 'candidate_v1'):
        raise ValueError('Unknown retriever')
    if code is not None and query is not None:
        raise ValueError('Choose either a section code or explicit keywords')
    for value, maximum in [(code, 100), (query, 2000)]:
        if value is not None and (not isinstance(value, str) or not 1 <= len(value.strip()) <= maximum):
            raise ValueError('Invalid explicit selector')
    db, manifest = verified_database(db)
    request = dict(question=question, retriever=retriever, code=code, query=query,
                   limit=limit, max_context_chars=max_context_chars)
    scope = assess_scope(question)
    evidence = None
    prompt = None
    status = 'unsupported_request'
    if scope['decision'] == 'allow':
        if retriever == 'candidate_v1':
            from grammar_editorial_search_candidate import prepare as retrieve
        else:
            retrieve = base.prepare
        evidence = retrieve(question, db=db, code=code, query=query, limit=limit,
                            max_context_chars=max_context_chars)
        status = evidence['status']
        if status == 'prepared':
            prompt = {'system_prompt': base.SYSTEM_PROMPT + '\n' + POLICY,
                      'user_payload': evidence['prompt_package']['user_payload']}
    return {'schema_version': 3, 'guard_version': GUARD_VERSION,
            'manifest_sha256': base.sha(db.parent / 'manifest.json'),
            'edition': manifest['edition']['edition'], 'request': request,
            'scope': scope, 'status': status, 'evidence_packet': evidence,
            'prompt_package': prompt, 'generation_called': False}

def validate_packet(packet, *, question, db=base.DEFAULT_DB):
    """Caller supplies its original question, not one read from the packet."""
    if not isinstance(packet, dict) or not isinstance(packet.get('request'), dict):
        raise ValueError('Invalid guarded packet')
    request = packet['request']
    if request.get('question') != question:
        raise ValueError('Question differs from caller request')
    if set(request) != {'question', 'retriever', 'code', 'query', 'limit', 'max_context_chars'}:
        raise ValueError('Invalid request fields')
    expected = prepare(db=db, **request)
    if canonical(packet) != canonical(expected):
        raise ValueError('Packet, prompt or provenance differs from replay')
    return {'valid': True, 'status': expected['status'],
            'semantic_correctness_assessed': False}

def require_fields(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError('Invalid ' + label + ' fields')

def citation_contexts(source, quote):
    body = strip_search_formatting(source['body'])
    positions = []
    offset = 0
    while (pos := body.find(quote, offset)) >= 0:
        positions.append(pos)
        offset = pos + 1
    return {'occurrences': len(positions), 'offset_basis': 'source body after strip_search_formatting',
            'section_code': source['code'], 'section_pdf_pages': source['pdf_pages'],
            'contexts': [{'start': pos, 'end': pos + len(quote),
                          'text': body[max(0, pos-120):pos+len(quote)+120]}
                         for pos in positions[:4]],
            'contexts_truncated': len(positions) > 4,
            'limits': '章节页范围，不是引句精确页定位；上下文存在不证明主张被充分支持。'}

def validate_response(packet, response, *, question, db=base.DEFAULT_DB):
    validate_packet(packet, question=question, db=db)
    if packet['status'] != 'prepared':
        raise ValueError('No generation-ready evidence')
    if not isinstance(response, dict):
        raise ValueError('Expected an answer object')
    if response.get('status') == 'insufficient_evidence':
        require_fields(response, ['status', 'message_zh'], 'insufficiency response')
        if not isinstance(response['message_zh'], str) or not response['message_zh'].strip():
            raise ValueError('Missing insufficiency reason')
        return {'valid': True, 'semantic_correctness_assessed': False, 'citation_contexts': []}
    require_fields(response, ['status', 'claims'], 'answer')
    claims = response['claims']
    if response['status'] != 'answered' or not isinstance(claims, list) or not 1 <= len(claims) <= 10:
        raise ValueError('Expected 1–10 evidenced claims')
    sources = {s['source_id']: s for s in packet['evidence_packet']['sources']}
    contexts = []
    for number, claim in enumerate(claims, 1):
        require_fields(claim, ['text_zh', 'citations'], 'claim')
        if not isinstance(claim['text_zh'], str) or not 1 <= len(claim['text_zh'].strip()) <= 6000:
            raise ValueError('Invalid claim text')
        citations = claim['citations']
        if not isinstance(citations, list) or not 1 <= len(citations) <= 20:
            raise ValueError('Claim missing bounded citation list')
        for citation in citations:
            require_fields(citation, ['source_id', 'quote'], 'citation')
            sid, quote = citation['source_id'], citation['quote']
            if not isinstance(sid, str) or sid not in sources or not isinstance(quote, str):
                raise ValueError('Invalid citation source or quote')
            if len(''.join(quote.split())) < 6 or quote not in strip_search_formatting(sources[sid]['body']):
                raise ValueError('Unsupported exact quote')
            contexts.append({'claim': number, 'source_id': sid, 'quote': quote,
                             **citation_contexts(sources[sid], quote)})
    return {'valid': True, 'semantic_correctness_assessed': False,
            'citation_contexts': contexts}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('question')
    parser.add_argument('--retriever', choices=['baseline', 'candidate_v1'], default='baseline')
    parser.add_argument('--code')
    parser.add_argument('--query')
    parser.add_argument('--limit', type=int, default=3)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = prepare(args.question, retriever=args.retriever, code=args.code,
                     query=args.query, limit=args.limit)
    output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        with args.output.open('x', encoding='utf-8') as handle:
            handle.write(output)
    else:
        print(output)
