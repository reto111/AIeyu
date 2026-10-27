"""Check local corpus provenance and a small engineering demonstration, not accuracy."""
from contextlib import closing
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
from datetime import datetime, timezone

from grammar_reference import rebuild_chunks

import tonglun_reference as corpus
import tonglun_rag as rag


def audit():
    db = corpus.WORK / 'tonglun_corpus.sqlite'
    records = {}
    with closing(sqlite3.connect(f'{db.resolve().as_uri()}?mode=ro', uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or conn.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('Raw database integrity failure')
        sources = {s['volume']: dict(s) for s in conn.execute('SELECT * FROM sources')}
        for v, source in sources.items():
            if corpus.file_sha256(Path(source['path'])) != source['sha256']:
                raise ValueError(f'Source changed: {v}')
            pages = {r[0] for r in conn.execute('SELECT pdf_page FROM raw_pages WHERE volume=?', (v,))}
            if pages != set(range(1, source['total_pages'] + 1)):
                raise ValueError(f'Incomplete raw coverage: {v}')
        for row in conn.execute('SELECT * FROM raw_pages ORDER BY volume,pdf_page'):
            v, p = row['volume'], row['pdf_page']
            path = corpus.volume_work(v) / 'raw' / f'p{p:04d}.json'
            record = json.loads(path.read_text(encoding='utf8'))
            if record != json.loads(row['record_json']):
                raise ValueError(f'Raw record changed: {v}/{p}')
            if record['source_sha256'] != sources[v]['sha256'] or record['text'] != row['text']:
                raise ValueError(f'Raw source/text mismatch: {v}/{p}')
            if record['status'] != 'unreviewed' or row['status'] != 'unreviewed':
                raise ValueError(f'Raw status promoted: {v}/{p}')
            if hashlib.sha256(row['text'].encode()).hexdigest() != row['text_sha256']:
                raise ValueError(f'Text hash mismatch: {v}/{p}')
            image = corpus.volume_work(v) / 'renders' / f'p{p:04d}.png'
            if corpus.file_sha256(image) != row['image_sha256']:
                raise ValueError(f'Image hash mismatch: {v}/{p}')
            records[(v, p)] = record
    exported = [json.loads(line) for line in (corpus.WORK / 'raw_pages.jsonl').read_text(encoding='utf8').splitlines()]
    if len(exported) != len(records) or {(r['volume'], r['pdf_page']): r for r in exported} != records:
        raise ValueError('JSONL export mismatch')
    reviewed, page_evidence, excluded = [], [], []
    for v in sources:
        db = corpus.reviewed_db(v)
        if not db.exists():
            continue
        with closing(sqlite3.connect(f'{db.resolve().as_uri()}?mode=ro', uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError(f'Review database integrity failure: {v}')
            # Recompute every state, including isolated units, in memory only.
            before = [tuple(r) for r in conn.execute('SELECT * FROM chunks ORDER BY code')]
            with closing(sqlite3.connect(':memory:')) as rebuilt:
                conn.backup(rebuilt)
                rebuild_chunks(rebuilt)
                after = rebuilt.execute('SELECT * FROM chunks ORDER BY code').fetchall()
            if before != after:
                raise ValueError(f'Stale section state or cross-page body: {v}')
            for row in conn.execute('SELECT * FROM batches'):
                candidates = []
                for path in (corpus.volume_work(v) / 'reviews').glob('*.json'):
                    batch = json.loads(path.read_text(encoding='utf8'))
                    if batch.get('batch_id') == row['id']:
                        candidates.append(batch)
                if len(candidates) != 1 or hashlib.sha256(json.dumps(candidates[0], ensure_ascii=False, sort_keys=True).encode()).hexdigest() != row['sha256']:
                    raise ValueError(f'Review batch changed: {row["id"]}')
            source = rag.core.read_source(conn)
            for row in conn.execute("SELECT code FROM chunks WHERE status='ready'"):
                reviewed.append(dict(volume=v, **rag.core.section_snapshot(conn, row['code'], source)))
            for row in conn.execute('SELECT * FROM pages'):
                page = json.loads(row['review_json'])
                if hashlib.sha256(row['review_json'].encode()).hexdigest() != row['review_sha256']:
                    raise ValueError(f'Page evidence changed: {v}/{row["pdf_page"]}')
                page_evidence.append(dict(volume=v, pdf_page=row['pdf_page'],
                    review_sha256=row['review_sha256'], scope=page.get('review_scope'),
                    original_render_sha256=records[(v, row['pdf_page'])]['image_sha256']))
            for row in conn.execute("SELECT code,title,status,notes,pdf_pages FROM chunks WHERE status!='ready'"):
                excluded.append(dict(volume=v, code=row['code'], title=row['title'],
                    status=row['status'], notes=json.loads(row['notes']), pdf_pages=json.loads(row['pdf_pages'])))
    corpus.dump(corpus.WORK / 'excluded_units.json', excluded)
    return dict(checked_at=datetime.now(timezone.utc).isoformat(),
        raw_database_integrity='ok', raw_records=len(records), raw_jsonl_matches=True,
        all_source_text_image_hashes_checked=True,
        volumes=[dict(volume=v, pages=s['total_pages'],
            ocr_pages=sum(r['volume'] == v and r['method'] == 'tesseract' for r in records.values()),
            direct_pages=sum(r['volume'] == v and r['method'] == 'direct' for r in records.values()),
            empty_text_pages=[r['pdf_page'] for r in records.values() if r['volume'] == v and not r['text']],
            source_sha256=s['sha256']) for v, s in sources.items()],
        reviewed_complete_units=len(reviewed), excluded_units=excluded,
        all_chunk_states_rebuilt_in_memory=True, visual_page_evidence=page_evidence,
        limits='完整性、来源及引用可追溯检查，不是OCR准确率、全书审核或生成答案质量验收。')


def demo(run_id):
    packet = rag.prepare('本书如何区分词汇学和词法学的研究对象？', '研究对象')
    if {s['volume'] for s in packet['sources']} != {1, 2}:
        raise ValueError('Expected both reviewed volume samples')
    # Several sections of the same volume can be returned. Keep the citation
    # attached to its actual code; never let a later result overwrite it.
    by_code = {s['code']: s for s in packet['sources']}
    lexical = by_code['v1.lexicology.ch01.unit01']
    morphology = by_code['v2.morphology.ch01.unit01']
    response = dict(status='answered', claims=[
        dict(text_zh='本书把以词汇作为研究对象的学科称为词汇学。', citations=[
            dict(source_id=lexical['source_id'], quote='语言学中以词汇作为研究对象的学科叫做词汇学（лексикология）。')]),
        dict(text_zh='本书说明词法学研究词的语法构造。', citations=[
            dict(source_id=morphology['source_id'], quote='词法学则是关于词的语法学说，研究的对象是词的语法构造。')])])
    checked = rag.validate(packet, response)
    bad = copy.deepcopy(response)
    bad['claims'][0]['citations'][0]['quote'] = '本书没有出现的伪造连续引文。'
    rejected = False
    try:
        rag.validate(packet, bad)
    except ValueError:
        rejected = True
    wrong_volume = copy.deepcopy(packet)
    wrong_volume['sources'][0]['volume'] = 3 - wrong_volume['sources'][0]['volume']
    wrong_rejected = False
    try:
        rag.validate(wrong_volume, response)
    except ValueError:
        wrong_rejected = True
    no_evidence = rag.prepare('量子计算机纠错编码如何实现？', '量子计算机纠错编码')
    budget = rag.prepare('本书如何区分词汇学和词法学？', '研究对象', max_context_chars=1)
    if not (rejected and wrong_rejected and no_evidence['status'] == 'no_evidence' and budget['status'] == 'context_over_budget'):
        raise ValueError('Demonstration gate failed')
    target = corpus.WORK / 'rag' / run_id
    corpus.dump(target / 'cross_volume_demo.json', packet)
    corpus.dump(target / 'cross_volume_response.json', response)
    corpus.dump(target / 'cross_volume_validation.json', checked)
    return dict(handwritten_demonstration_not_generation=True, artifact_directory=str(target), cited_volumes=[1, 2],
        valid_quotes_checked=2, forged_quote_rejected=rejected, wrong_volume_rejected=wrong_rejected,
        unrelated_question=no_evidence['status'], whole_section_budget_gate=budget['status'],
        limits='围绕已读样例的工程演示，不是独立留出题、召回率或生成准确率实验。')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = args.output or corpus.WORK / f'verification_{datetime.now(timezone.utc):%Y%m%d_%H%M%S_%f}.json'
    if output.exists():
        raise ValueError('Verification report is immutable; choose another output path')
    result = audit()
    result['engineering_demo'] = demo(output.stem)
    corpus.dump(output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
