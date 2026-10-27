"""Resumable local two-volume corpus; raw OCR is excluded from reviewed search."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess

import pymupdf

from extract_pdf_text import TESSERACT_EXE, TESSDATA_DIR, render_page
from grammar_reference import dump, import_batch, normalize, search
from knowledge_base import file_sha256

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'data/processed/tonglun_reference'
SOURCES = {v: ROOT / f'data/knowledge_sources/xinshidaieyutonglun{v}.pdf' for v in (1, 2)}
# Ranges inferred from the visually inspected contents and endpoint pages.
# Printed pagination inside these ranges still needs page-by-page confirmation.
LAYOUT = {
    1: [(1, 4, 'cover_and_imprint'), (5, 7, 'preface'), (8, 16, 'contents'),
        (17, 27, 'body'), (28, 28, 'visually_confirmed_blank'), (29, 385, 'body'),
        (386, 401, 'terminology'), (402, 404, 'bibliography'),
        (405, 405, 'digital_appendix')],
    2: [(1, 4, 'cover_and_imprint'), (5, 13, 'contents'), (14, 166, 'body'),
        (167, 167, 'visually_confirmed_blank'), (168, 382, 'body'),
        (383, 392, 'terminology'), (393, 395, 'bibliography'), (396, 396, 'digital_appendix')],
}


def source_title(volume):
    return f'新时代俄语通论（{"上" if volume == 1 else "下"}册，张家骅主编，商务印书馆，2006）'


def volume_work(volume):
    return WORK / f'volume{volume}'


def reviewed_db(volume):
    return volume_work(volume) / 'reviewed.sqlite'


def inventory():
    sources = []
    for v, path in SOURCES.items():
        with pymupdf.open(path) as doc:
            pages = [dict(pdf_page=i + 1, direct_chars=len(p.get_text().strip())) for i, p in enumerate(doc)]
        record = dict(volume=v, title=source_title(v), path=str(path.resolve()),
                      source_sha256=file_sha256(path), total_pages=len(pages), pages=pages)
        target = volume_work(v) / 'source.json'
        if target.exists() and json.loads(target.read_text(encoding='utf8'))['source_sha256'] != record['source_sha256']:
            raise ValueError(f'Source changed: volume {v}')
        dump(target, record)
        sources.append(record)
    return sources


def extract_one(v, page, fingerprint, dpi):
    target = volume_work(v) / 'raw' / f'p{page:04d}.json'
    if target.exists():
        old = json.loads(target.read_text(encoding='utf8'))
        if (old['source_sha256'], old['pdf_page'], old['volume'], old['dpi']) != (fingerprint, page, v, dpi):
            raise ValueError(f'Cache identity/configuration differs: {target}')
        if hashlib.sha256(old['text'].encode()).hexdigest() != old['text_sha256']:
            raise ValueError(f'Cache text changed: {target}')
        return
    with pymupdf.open(SOURCES[v]) as doc:
        direct = doc[page - 1].get_text().strip()
        image = volume_work(v) / 'renders' / f'p{page:04d}.png'
        image.parent.mkdir(parents=True, exist_ok=True)
        render_page(doc[page - 1], image, dpi)
    method = 'direct' if direct else 'tesseract'
    if direct:
        text = direct
    else:
        env = os.environ.copy()
        env['OMP_THREAD_LIMIT'] = '1'
        result = subprocess.run([str(TESSERACT_EXE), str(image), 'stdout',
            '--tessdata-dir', str(TESSDATA_DIR), '-l', 'chi_sim+rus+eng', '--psm', '6'],
            capture_output=True, check=True, text=True, encoding='utf8', timeout=180, env=env)
        text = result.stdout.strip()
    dump(target, dict(volume=v, pdf_page=page, printed_page=None, source_sha256=fingerprint,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(), image_sha256=file_sha256(image),
        method=method, dpi=dpi, languages='chi_sim+rus+eng' if not direct else None,
        psm=6 if not direct else None, status='unreviewed',
        created_at=datetime.now(timezone.utc).isoformat(), text=text))


def extract(volumes, start, end, workers, dpi):
    sources = inventory()
    tasks = [(s['volume'], p, s['source_sha256'], dpi) for s in sources if s['volume'] in volumes
             for p in range(start, min(end or s['total_pages'], s['total_pages']) + 1)]
    errors = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(extract_one, *task): task for task in tasks}
        for n, future in enumerate(as_completed(futures), 1):
            task = futures[future]
            try:
                future.result()
            except Exception as exc:
                errors.append(dict(volume=task[0], pdf_page=task[1], error=str(exc)))
                print(json.dumps(errors[-1], ensure_ascii=False), flush=True)
            if n % 25 == 0 or n == len(tasks):
                print(json.dumps(dict(completed=n, scheduled=len(tasks), errors=len(errors))), flush=True)
    dump(WORK / 'last_extraction.json', dict(scheduled=len(tasks), errors=errors))
    if errors:
        raise RuntimeError(f'{len(errors)} pages failed; successful pages retained for resume')


def build_corpus():
    with closing(sqlite3.connect(':memory:')) as conn:
        return _build_corpus(conn)


def _build_corpus(conn):
    sources = inventory()
    conn.executescript('''
      CREATE TABLE sources(volume INTEGER PRIMARY KEY, title TEXT NOT NULL,
        path TEXT NOT NULL, sha256 TEXT NOT NULL, total_pages INTEGER NOT NULL);
      CREATE TABLE raw_pages(volume INTEGER NOT NULL REFERENCES sources(volume),
        pdf_page INTEGER NOT NULL, printed_page TEXT, method TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status='unreviewed'), text TEXT NOT NULL,
        text_sha256 TEXT NOT NULL, image_sha256 TEXT NOT NULL, record_json TEXT NOT NULL,
        PRIMARY KEY(volume,pdf_page));
    ''')
    for source in sources:
        v = source['volume']
        conn.execute('INSERT INTO sources VALUES(?,?,?,?,?)',
            (v, source['title'], source['path'], source['source_sha256'], source['total_pages']))
        for path in sorted((volume_work(v) / 'raw').glob('p*.json')):
            record = json.loads(path.read_text(encoding='utf8'))
            if record['source_sha256'] != source['source_sha256'] or record['volume'] != v:
                raise ValueError(f'Source mismatch: {path}')
            if not 1 <= record['pdf_page'] <= source['total_pages']:
                raise ValueError(f'Invalid page: {path}')
            if hashlib.sha256(record['text'].encode()).hexdigest() != record['text_sha256']:
                raise ValueError(f'Text hash mismatch: {path}')
            image = volume_work(v) / 'renders' / f"p{record['pdf_page']:04d}.png"
            if file_sha256(image) != record['image_sha256']:
                raise ValueError(f'Image hash mismatch: {path}')
            conn.execute('INSERT INTO raw_pages VALUES(?,?,?,?,?,?,?,?,?)',
                (v, record['pdf_page'], record['printed_page'], record['method'], 'unreviewed',
                 record['text'], record['text_sha256'], record['image_sha256'], json.dumps(record, ensure_ascii=False)))
    conn.commit()
    if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or conn.execute('PRAGMA foreign_key_check').fetchall():
        raise ValueError('Corpus integrity failure')
    target = WORK / 'tonglun_corpus.sqlite'
    if target.exists():
        backup = WORK / 'backups' / f'corpus_{datetime.now():%Y%m%d_%H%M%S_%f}.sqlite'
        backup.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(target)) as old, closing(sqlite3.connect(backup)) as saved:
            old.backup(saved)
    with closing(sqlite3.connect(target)) as out:
        conn.backup(out)
    with (WORK / 'raw_pages.jsonl').open('w', encoding='utf8') as stream:
        for (record,) in conn.execute('SELECT record_json FROM raw_pages ORDER BY volume,pdf_page'):
            stream.write(record + '\n')
    return status()


def status():
    report = dict(volumes=[], raw_is_reviewed=False)
    for v in (1, 2):
        source_path = volume_work(v) / 'source.json'
        if not source_path.exists():
            continue
        source = json.loads(source_path.read_text(encoding='utf8'))
        done = [json.loads(p.read_text(encoding='utf8'))['pdf_page'] for p in (volume_work(v) / 'raw').glob('p*.json')]
        item = dict(volume=v, total_pages=source['total_pages'], extracted_pages=len(done),
                    missing_pages=sorted(set(range(1, source['total_pages'] + 1)) - set(done)),
                    reviewed_pages=0, whole_body_reviewed_pages=0, partial_review_pages=0, chunks={})
        db = reviewed_db(v)
        if db.exists():
            with closing(sqlite3.connect(f'{db.resolve().as_uri()}?mode=ro', uri=True)) as conn:
                item['reviewed_pages'] = conn.execute('SELECT count(*) FROM pages').fetchone()[0]
                records = [json.loads(row[0]) for row in conn.execute('SELECT review_json FROM pages')]
                item['whole_body_reviewed_pages'] = sum(p.get('review_scope') == 'whole_body_on_page' for p in records)
                item['partial_review_pages'] = len(records) - item['whole_body_reviewed_pages']
                item['chunks'] = dict(conn.execute('SELECT status,count(*) FROM chunks GROUP BY status'))
        report['volumes'].append(item)
    dump(WORK / 'checkpoint.json', report)
    return report


def retrieve(query, limit=5, include_unreviewed=False):
    if limit < 1:
        return []
    if not include_unreviewed:
        hits = []
        for v in (1, 2):
            if reviewed_db(v).exists():
                hits.extend(dict(hit, volume=v) for hit in search(query, limit, reviewed_db(v)))
        return sorted(hits, key=lambda h: (-h['score'], h['volume'], h['code']))[:limit]
    terms = [normalize(t) for t in query.split() if t]
    if not terms:
        return []
    hits = []
    db = WORK / 'tonglun_corpus.sqlite'
    with closing(sqlite3.connect(f'{db.resolve().as_uri()}?mode=ro', uri=True)) as conn:
        for v, p, text in conn.execute('SELECT volume,pdf_page,text FROM raw_pages'):
            # Both supplied scans append a non-book digital provenance page.
            # Preserve it in the raw archive; exclude it from book-text lookup.
            total, = conn.execute('SELECT total_pages FROM sources WHERE volume=?', (v,)).fetchone()
            if (v, total, p) in ((1, 405, 405), (2, 396, 396)):
                continue
            normalized = normalize(text)
            if all(t in normalized for t in terms):
                hits.append(dict(volume=v, pdf_page=p, text=text, status='unreviewed',
                    score=sum(min(normalized.count(t), 10) for t in terms),
                    citation=f'{source_title(v)}，PDF {p} 页（未审核OCR，不作论文定稿引文）'))
    return sorted(hits, key=lambda h: (-h['score'], h['volume'], h['pdf_page']))[:limit]


def export():
    """Readable raw/reviewed layers and explicit page-level remaining-work queue."""
    from grammar_rag import read_source, section_snapshot
    report = status()
    queue, units, metadata = [], [], []
    for source in inventory():
        v = source['volume']
        pages = {}
        if reviewed_db(v).exists():
            with closing(sqlite3.connect(f'{reviewed_db(v).resolve().as_uri()}?mode=ro', uri=True)) as conn:
                conn.row_factory = sqlite3.Row
                pages = {r['pdf_page']: json.loads(r['review_json']) for r in conn.execute('SELECT * FROM pages')}
                source_record = read_source(conn)
                for row in conn.execute("SELECT code FROM chunks WHERE status='ready' ORDER BY code"):
                    units.append(dict(volume=v, **section_snapshot(conn, row['code'], source_record)))
        lines = [f'# {source_title(v)}：未审核提取文本', '',
                 '逐页OCR或文字层原始提取，保留识别错误，不可作为已核验论文引文。', '']
        for p in range(1, source['total_pages'] + 1):
            raw = volume_work(v) / 'raw' / f'p{p:04d}.json'
            role = next((role for a, b, role in LAYOUT[v] if a <= p <= b), 'unknown')
            page = pages.get(p)
            state = 'whole_body_checked' if page and page.get('review_scope') == 'whole_body_on_page' else 'partial_checked' if page else 'unreviewed'
            if role in ('body', 'terminology', 'bibliography'):
                queue.append(dict(volume=v, pdf_page=p, role=role,
                    printed_page=page.get('printed_page') if page else None,
                    printed_page_candidate=p - (16 if v == 1 else 13),
                    candidate_pagination_verified=bool(page), status=state,
                    raw_exists=raw.exists(), render=str(volume_work(v) / 'renders' / f'p{p:04d}.png')))
            if raw.exists():
                record = json.loads(raw.read_text(encoding='utf8'))
                lines.extend([f'## PDF {p} / {role} / unreviewed', '', record['text'], ''])
        (volume_work(v) / 'raw_pages.md').write_text('\n'.join(lines), encoding='utf8')
        metadata.append(dict(volume=v, title=source['title'], source_sha256=source['source_sha256'],
            total_pages=source['total_pages'], role_ranges=LAYOUT[v],
            role_basis='原图封面/目录/正文起点与末页定位；非逐页印刷页审核'))
    with (WORK / 'reviewed_units.jsonl').open('w', encoding='utf8') as stream:
        for unit in units:
            stream.write(json.dumps(unit, ensure_ascii=False) + '\n')
    lines = ['# 新时代俄语通论：已核验完整单元', '', '只包含当前ready单元；不代表全书已审核。', '']
    for unit in units:
        lines.extend([f"## {unit['title']}", '', unit['citation'], '', unit['body'], ''])
    (WORK / 'reviewed_units.md').write_text('\n'.join(lines), encoding='utf8')
    dump(WORK / 'review_queue.json', dict(pagination_note='候选页码不得冒充原图逐页核验；正文范围含编章扉页。', pages=queue))
    dump(WORK / 'source_catalog.json', metadata)
    return dict(checkpoint=report, ready_units=len(units), queued_pages=len(queue),
                queue_status={s: sum(p['status'] == s for p in queue)
                              for s in ('whole_body_checked', 'partial_checked', 'unreviewed')})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('inventory')
    p = sub.add_parser('extract')
    p.add_argument('--volume', type=int, choices=(1, 2))
    p.add_argument('--start', type=int, default=1)
    p.add_argument('--end', type=int)
    p.add_argument('--workers', type=int, default=4)
    p.add_argument('--dpi', type=int, default=220)
    sub.add_parser('build')
    sub.add_parser('status')
    sub.add_parser('export')
    p = sub.add_parser('import')
    p.add_argument('batch', type=Path)
    p.add_argument('--volume', type=int, choices=(1, 2), required=True)
    p.add_argument('--apply', action='store_true')
    p = sub.add_parser('search')
    p.add_argument('query')
    p.add_argument('--limit', type=int, default=5)
    p.add_argument('--include-unreviewed', action='store_true')
    args = parser.parse_args()
    if args.command == 'inventory':
        result = [{k: v for k, v in s.items() if k != 'pages'} for s in inventory()]
    elif args.command == 'extract':
        if args.start < 1 or not 1 <= args.workers <= 8 or args.dpi < 72 or (args.end is not None and args.end < args.start):
            parser.error('Invalid page range, workers (1-8), or dpi (>=72)')
        extract([args.volume] if args.volume else [1, 2], args.start, args.end, args.workers, args.dpi)
        result = build_corpus()
    elif args.command == 'build':
        result = build_corpus()
    elif args.command == 'export':
        result = export()
    elif args.command == 'import':
        result = import_batch(args.batch, db=reviewed_db(args.volume), apply=args.apply,
                              pdf=SOURCES[args.volume], title=source_title(args.volume))
        status()
    elif args.command == 'search':
        result = retrieve(args.query, args.limit, args.include_unreviewed)
    else:
        result = status()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
