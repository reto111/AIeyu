"""Optional local lexical question baseline for Tonglun; no default-route changes."""
from __future__ import annotations

import argparse
from contextlib import closing
import json
import math
from pathlib import Path
import re
import sqlite3
import unicodedata

from grammar_reference import normalize
import grammar_rag as core
import tonglun_reference as corpus
import tonglun_rag as rag

CHINESE = re.compile(r'[\u4e00-\u9fff]+(?:[—－-][\u4e00-\u9fff]+)*')
RUSSIAN = re.compile(r'[а-яё]+')
SUFFIXES = ('的具体语法意义', '的抽象语法意义', '的表现形式', '的构成方式',
            '的概念', '的类别', '的种类', '的特点', '的功能', '的作用', '的定义',
            '的形式', '的用法', '的语义', '概述')
GENERIC = frozenset(('概述', '概念', '类别', '种类', '特点', '功能', '作用', '定义',
                     '意义', '形式', '用法', '基本特征', '绪论'))


def norm(text):
    return unicodedata.normalize('NFC', normalize(text))


def title_terms(titles):
    """Surface topic forms from catalog titles, without body text or glossary."""
    topics = set()
    for title in titles:
        for part in title.split('/'):
            part = re.sub(r'^\s*(?:第[一二三四五六七八九十百零\d]+[编章节]|\d+[.．、）)])\s*', '', part)
            for word in CHINESE.findall(part):
                candidates = [word]
                for suffix in SUFFIXES:
                    if word.endswith(suffix):
                        candidates.append(word[:-len(suffix)])
                candidates.extend(re.split('[、和与]', word))
                for candidate in candidates:
                    if 2 <= len(candidate) <= 24 and candidate not in GENERIC:
                        topics.add(candidate)
    forms = {}
    for topic in sorted(topics):
        variants = {topic}
        if any(char in topic for char in '—－-'):
            variants |= {re.sub('[—－-]', separator, topic) for separator in ('', '—', '－', '-')}
        forms[topic] = tuple(sorted(norm(x) for x in variants))
    return forms


def extract_terms(question, forms):
    text = norm(question)
    covered, found = set(), []
    candidates = [(form, topic) for topic, variants in forms.items() for form in variants]
    for form, topic in sorted(candidates, key=lambda x: (-len(x[0]), x[0], x[1])):
        for match in re.finditer(re.escape(form), text):
            span = set(range(match.start(), match.end()))
            if not span & covered:
                covered |= span
                found.append((match.start(), topic))
    found += [(match.start(), match.group()) for match in RUSSIAN.finditer(text)]
    return list(dict.fromkeys(term for _, term in sorted(found)))[:12]


def term_count(term, text, forms):
    if RUSSIAN.fullmatch(term):
        return len(re.findall(r'(?<![а-яё])' + re.escape(term) + r'(?![а-яё])', text))
    return max((text.count(form) for form in forms.get(term, (norm(term),))), default=0)


def search_question(question, limit=3):
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 2000:
        raise ValueError('Question must contain 1–2000 characters')
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ValueError('Limit must be 1–10')
    titles, rows = [], []
    for volume in (1, 2):
        with closing(sqlite3.connect(corpus.reviewed_db(volume).resolve().as_uri() + '?mode=ro', uri=True)) as db:
            db.row_factory = sqlite3.Row
            db.execute('BEGIN')
            for item in db.execute('SELECT code,title,body,status FROM chunks ORDER BY code'):
                titles.append(item['title'])
                if item['status'] == 'ready':
                    rows.append(dict(item, volume=volume))
    forms = title_terms(titles)
    terms = extract_terms(question, forms)
    if not terms:
        return [], terms
    documents = [(row, norm(row['title'].split('/')[-1]), norm(row['title']), norm(row['body'])) for row in rows]
    counts = [(row, {t: (term_count(t, leaf, forms), term_count(t, title, forms), term_count(t, body, forms)) for t in terms})
              for row, leaf, title, body in documents]
    weights = {t: 1 + math.log((len(rows) + 1) / (1 + sum(any(values[t]) for _, values in counts))) for t in terms}
    hits = []
    for row, values in counts:
        matched = [term for term in terms if any(values[term])]
        if not matched:
            continue
        score = sum(weights[t] * (3 * bool(values[t][0]) + bool(values[t][1]) + 1 + min(values[t][2], 3)/3) for t in matched)
        hits.append(dict(volume=row['volume'], code=row['code'], title=row['title'], body=row['body'],
                         score=round(score, 8), matched_terms=matched,
                         unmatched_terms=[term for term in terms if term not in matched]))
    return sorted(hits, key=lambda x: (-x['score'], x['volume'], x['code']))[:limit], terms


def prepare(question, limit=3, max_context_chars=16000):
    if type(max_context_chars) is not int or max_context_chars < 1:
        raise ValueError('Positive whole-section context budget required')
    hits, terms = search_question(question, limit)
    sources, omitted, used = [], [], 0
    for hit in hits:
        with closing(sqlite3.connect(corpus.reviewed_db(hit['volume']).resolve().as_uri() + '?mode=ro', uri=True)) as db:
            db.row_factory = sqlite3.Row
            db.execute('BEGIN')
            source = core.section_snapshot(db, hit['code'], core.read_source(db))
        if source['body'] != hit['body']:
            raise ValueError('Retrieval source changed; prepare again')
        if used + len(source['body']) > max_context_chars:
            omitted.append(dict(volume=hit['volume'], code=hit['code'], reason='whole_section_exceeds_budget'))
            continue
        used += len(source['body'])
        sources.append(dict(source_id=f'T{len(sources)+1}', volume=hit['volume'], **source))
    status = 'prepared' if sources else 'context_over_budget' if omitted else 'no_evidence'
    return dict(schema_version=1, status=status, question=question.strip(), query=None,
                retrieval=dict(mode='question_lexical_candidate', terms=terms,
                               vocabulary_origin='all_catalog_titles_query_recognition_only',
                               scoring='fixed_title_and_capped_body_counts_with_idf'),
                sources=sources, omitted_sections=omitted, context_characters=used,
                limits='独立可选词面候选，未改变默认入口。仅用目录标题识别中文主题、按完整俄语词形匹配；不做语义理解、词形还原或证据充分性判断。隔离单元与附录候选不作来源；有词面命中仍可能范围外，需另做评价。未调用生成模型。',
                prompt_package=dict(system_prompt=rag.SYSTEM_PROMPT, user_payload=dict(question=question.strip(), retrieved_sources=sources)) if sources else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--question', required=True)
    parser.add_argument('--limit', type=int, default=3)
    parser.add_argument('--max-context-chars', type=int, default=16000)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    packet = prepare(args.question, args.limit, args.max_context_chars)
    with args.output.open('x', encoding='utf8') as handle:
        handle.write(json.dumps(packet, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(status=packet['status'], terms=packet['retrieval']['terms'], source_count=len(packet['sources']), output=str(args.output)), ensure_ascii=False))


if __name__ == '__main__':
    main()
