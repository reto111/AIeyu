"""Locate exact editorial quotes in verified page transcripts, preserving edits.

Offsets refer to transcribed characters, never PDF glyph coordinates. A derived
page anchor for revised characters is not a claim that the PDF prints them.
"""
from __future__ import annotations
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3

from grammar_editorial_rag import DEFAULT_DB, snapshot, verify_package, thash
from grammar_reference import strip_search_formatting

MARKERS = frozenset('*`')

def trace_section(conn, code):
    source = snapshot(conn, code)
    raw = json.loads(conn.execute('SELECT row_json FROM editorial_raw_sections WHERE code=?', (code,)).fetchone()[0])
    raw_body = raw['body']
    labels = []
    pages = []
    offset = 0
    raw_normalized_index = 0
    for page in json.loads(raw['pdf_pages']):
        record = conn.execute('SELECT review_json,printed_page,review_sha256 FROM pages WHERE pdf_page=?', (page,)).fetchone()
        review = json.loads(record['review_json'])
        fragment = next(f for f in review['fragments'] if f['code'] == code)
        text = fragment['body']; page_set = frozenset([page])
        pages.append({'pdf_page': page, 'printed_page': record['printed_page'],
                      'raw_start': offset, 'raw_end': offset+len(text),
                      'page_review_sha256': record['review_sha256']})
        for char in text:
            # raw-normalized positions let us detect a quote joined across a
            # deleted span even when all remaining characters are unchanged.
            norm_index = None if char in MARKERS else raw_normalized_index
            labels.append((page_set, offset, norm_index))
            offset += 1
            if char not in MARKERS:
                raw_normalized_index += 1
    if offset != len(raw_body):
        raise ValueError('Raw page length mismatch')
    body = raw_body
    row = conn.execute('SELECT metadata_json FROM editorial_sections WHERE code=?', (code,)).fetchone()
    if row:
        for group in json.loads(row[0])['changes']:
            for edit in reversed(group['edits']):
                start, old, new = edit['start'], edit['old'], edit['new']
                end = start+len(old)
                if body[start:end] != old:
                    raise ValueError('Editorial replay conflict')
                anchors = labels[start:end] if old else labels[max(0,start-1):min(len(labels),start+1)]
                touched = frozenset(p for label in anchors for p in label[0])
                if new and not touched:
                    raise ValueError('Unanchored insertion')
                body = body[:start]+new+body[end:]
                labels[start:end] = [(touched,None,None)]*len(new)
    if body != source['body'] or len(body) != len(labels):
        raise ValueError('Editorial provenance replay mismatch')
    normalized_body = strip_search_formatting(body)
    normalized_labels = [label for char,label in zip(body,labels) if char not in MARKERS]
    if len(normalized_body) != len(normalized_labels):
        raise ValueError('Quote representation mismatch')
    return {'source': source, 'raw_normalized_body': strip_search_formatting(raw_body),
            'normalized_body': normalized_body, 'labels': normalized_labels, 'pages': pages}

def locate_in_trace(trace, quote):
    if not isinstance(quote,str) or not quote:
        raise ValueError('Nonempty exact quote required')
    body = trace['normalized_body'];labels = trace['labels'];source = trace['source']
    hits = [];offset = 0
    while (start := body.find(quote,offset)) >= 0:
        end = start+len(quote); selected = labels[start:end]
        touched = sorted({page for label in selected for page in label[0]})
        indices = [label[2] for label in selected]
        raw_exact = all(i is not None for i in indices) and all(b == a+1 for a,b in zip(indices,indices[1:]))
        if raw_exact:
            raw_exact = trace['raw_normalized_body'][indices[0]:indices[-1]+1] == quote
        hits.append({'occurrence':len(hits)+1,'normalized_start':start,'normalized_end':end,
                     'pdf_pages':touched,
                     'printed_pages':[p['printed_page'] for p in trace['pages'] if p['pdf_page'] in touched],
                     'provenance_kind':'literal_transcription_span' if raw_exact else 'editorial_derived_span',
                     'literal_in_original_at_this_span':bool(raw_exact),
                     'contains_replacement_characters':any(label[1] is None for label in selected),
                     'page_evidence':[{'pdf_page':p['pdf_page'],'page_review_sha256':p['page_review_sha256']}
                                      for p in trace['pages'] if p['pdf_page']in touched]})
        offset = start+1
    return {'code':source['code'],'quote':quote,'source_body_sha256':source['body_sha256'],
            'source_content_kind':source['content_kind'],'section_pdf_pages':source['pdf_pages'],
            'quote_found':bool(hits),'occurrences':hits,'ambiguous':len(hits)>1,
            'limits':'基于已核验页转录和编校日志；不是PDF字形坐标。编校字符的页为来源锚定，不表示原PDF逐字印有该引句。'}

def locate(code,quote,*,db=DEFAULT_DB):
    db=Path(db).resolve();verify_package(db.parent)
    with closing(sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)) as conn:
        conn.row_factory=sqlite3.Row
        return locate_in_trace(trace_section(conn,code),quote)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('code');parser.add_argument('quote');parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=locate(args.code,args.quote)
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        with args.output.open('x',encoding='utf-8')as handle:handle.write(text)
    else:print(text)
