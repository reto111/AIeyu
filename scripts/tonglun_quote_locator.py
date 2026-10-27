"""Locate exact quotes in ready Tonglun page transcripts, without network calls."""
from __future__ import annotations

import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3

import grammar_rag as core
from grammar_reference import strip_search_formatting
import tonglun_reference as corpus

MARKERS = frozenset('*`')


def trace_ready_section(conn, code, source):
    snapshot = core.section_snapshot(conn, code, source)
    labels, pages, bodies = [], [], []
    raw_offset = 0
    for page in snapshot['pdf_pages']:
        record = conn.execute('SELECT review_json,review_sha256 FROM pages WHERE pdf_page=?', (page,)).fetchone()
        review = json.loads(record['review_json'])
        fragment = next(f for f in review['fragments'] if f['code'] == code)
        text = fragment['body']
        pages.append(dict(pdf_page=page, printed_page=review.get('printed_page'),
                          page_review_sha256=record['review_sha256']))
        for local_offset, char in enumerate(text):
            if char not in MARKERS:
                labels.append((page, local_offset, raw_offset + local_offset))
        bodies.append(text)
        raw_offset += len(text)
    body = ''.join(bodies)
    if body != snapshot['body']:
        raise ValueError('Page reconstruction mismatch')
    normalized = strip_search_formatting(body)
    if len(normalized) != len(labels):
        raise ValueError('Quote representation mismatch')
    return dict(source=snapshot, normalized_body=normalized, labels=labels, pages=pages)


def locate_in_trace(trace, quote):
    if not isinstance(quote, str) or not quote.strip() or len(quote) > 1024:
        raise ValueError('An exact quote of 1–1024 characters is required')
    hits, offset = [], 0
    while (start := trace['normalized_body'].find(quote, offset)) >= 0:
        end = start + len(quote)
        selected = trace['labels'][start:end]
        touched = sorted({label[0] for label in selected})
        fragments = []
        for page in touched:
            positions = [label[1] for label in selected if label[0] == page]
            fragments.append(dict(pdf_page=page, fragment_start=min(positions), fragment_end=max(positions) + 1))
        hits.append(dict(occurrence=len(hits) + 1, normalized_start=start, normalized_end=end,
                         pdf_pages=touched, page_fragment_spans=fragments,
                         page_evidence=[p for p in trace['pages'] if p['pdf_page'] in touched]))
        offset = start + 1
    source = trace['source']
    return dict(code=source['code'], quote=quote, source_body_sha256=source['body_sha256'],
                source_sha256=source['source_sha256'], section_pdf_pages=source['pdf_pages'],
                quote_found=bool(hits), occurrences=hits, ambiguous=len(hits) > 1,
                content_kind='reviewed_transcription',
                limits='按当前ready单元和逐页审核转录定位；正文仅去除*和`排版标记。保留重音、ё、空格与换行，跨页引句保留全部页。偏移为Unicode字符索引，片段范围包含夹在其中的排版标记；不是PDF字形坐标或原印逐字正确率，也不证明引句支持主张。')


def locate(volume, code, quote):
    if type(volume) is not int or volume not in (1, 2):
        raise ValueError('Volume must be 1 or 2')
    with closing(sqlite3.connect(corpus.reviewed_db(volume).resolve().as_uri() + '?mode=ro', uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute('BEGIN')
        source = core.read_source(conn)
        if Path(source['path']).resolve() != corpus.SOURCES[volume].resolve():
            raise ValueError('Source volume mismatch')
        result = locate_in_trace(trace_ready_section(conn, code, source), quote)
    return dict(volume=volume, **result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('volume', type=int, choices=(1, 2))
    parser.add_argument('code')
    parser.add_argument('quote')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = locate(args.volume, args.code, args.quote)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        with args.output.open('x', encoding='utf8') as handle:
            handle.write(payload)
    else:
        print(payload, end='')


if __name__ == '__main__':
    main()
