"""Read-only full-book coverage/provenance audit and local issue queue export."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from grammar_reference import DB, PDF, WORK, dump, file_sha256, now

METADATA_FILES = (
    'frontmatter_001_004.json', 'toc_005_008.json', 'toc_009_012.json',
    'toc_013_016.json', 'toc_017_020.json', 'layout_021_022.json',
    'layout_406_408.json', 'backmatter_639_641.json',
)


def audit(db=DB, pdf=PDF, work=WORK):
    db, pdf, work = Path(db), Path(pdf), Path(work)
    fingerprint = file_sha256(pdf)
    issues, body_pages, starts, ends, fragments = [], set(), {}, {}, {}
    page_evidence = {}
    with closing(sqlite3.connect(f'{db.resolve().as_uri()}?mode=ro', uri=True)) as conn:
        source = conn.execute('SELECT sha256,total_pages FROM source').fetchone()
        assert source[0] == fingerprint, 'PDF fingerprint differs'
        assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not conn.execute('PRAGMA foreign_key_check').fetchall()
        chunks = {code: dict(title=title, status=status, pages=json.loads(pages))
                  for code, title, status, pages in conn.execute(
                      'SELECT code,title,status,pdf_pages FROM chunks')}
        batches = dict(conn.execute('SELECT id,sha256 FROM batches'))
        for n, raw, digest, batch in conn.execute(
                'SELECT pdf_page,review_json,review_sha256,batch_id FROM pages ORDER BY pdf_page'):
            assert hashlib.sha256(raw.encode()).hexdigest() == digest, f'Page hash {n}'
            p = json.loads(raw)
            assert p['pdf_page'] == n and p['review_method'] == 'visual_comparison'
            assert batch in batches
            page_evidence[n] = (batch, digest)
            body_pages.add(n)
            for f in p['fragments']:
                code = f['code']
                assert chunks[code]['title'] == f['title'], f'Title mismatch {code}'
                fragments.setdefault(code, []).append(n)
                if f.get('start'):
                    assert code not in starts, f'Duplicate start {code}'
                    starts[code] = n
                if f.get('end'):
                    assert code not in ends, f'Duplicate end {code}'
                    ends[code] = n
                for note in f.get('unresolved', []) + p.get('unresolved', []):
                    assert chunks[code]['status'] == 'unresolved', f'Unblocked issue {code}'
                    issues.append(dict(code=code, title=f['title'], pdf_page=n,
                        printed_page=p.get('printed_page'), note=note,
                        review_sha256=digest, batch_id=batch,
                        image_path=(work/'renders'/f'p{n:04}.png').resolve().as_posix()))
        revisions = conn.execute('SELECT pdf_page,previous_json,previous_sha256,'
            'previous_batch_id,correction_batch_id FROM page_revisions').fetchall()
        for n, raw, digest, previous_batch, correction_batch in revisions:
            assert hashlib.sha256(raw.encode()).hexdigest() == digest, f'Revision hash {n}'
            assert previous_batch in batches and correction_batch in batches
    for code, pages in fragments.items():
        assert code in starts and code in ends, f'Unfinished section {code}'
        assert pages == list(range(starts[code], ends[code]+1)), f'Page gap {code}'
        assert chunks[code]['pages'] == pages, f'Chunk provenance mismatch {code}'
    batch_files, batch_pages = {}, {}
    for path in (work/'reviews').glob('batch*.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        key = data['batch_id']
        if key in batches:
            canonical = json.dumps(data, ensure_ascii=False, sort_keys=True).encode()
            assert hashlib.sha256(canonical).hexdigest() == batches[key], f'Batch changed {key}'
            batch_files[key] = path.name
            batch_pages[key] = {p['pdf_page']: hashlib.sha256(json.dumps(
                p, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
                for p in data['pages']}
    assert set(batch_files) == set(batches), 'Missing imported batch evidence'
    for n, (batch, digest) in page_evidence.items():
        assert batch_pages[batch][n] == digest, f'Page differs from source batch {n}'
    for n, raw, digest, previous_batch, correction_batch in revisions:
        assert batch_pages[previous_batch][n] == digest, f'Revision differs from batch {n}'
        assert n in batch_pages[correction_batch]
    metadata, metadata_hashes = [], {}
    for name in METADATA_FILES:
        path = work/'reviews'/name
        data = json.loads(path.read_text(encoding='utf-8'))
        assert data['source_sha256'] == fingerprint
        assert data['review_method'] == 'visual_comparison'
        metadata.extend(data['pages'])
        metadata_hashes[name] = file_sha256(path)
    nonbody = [p['pdf_page'] for p in metadata]
    assert len(nonbody) == len(set(nonbody))
    assert not body_pages.intersection(nonbody)
    missing = sorted(set(range(1, source[1]+1))-body_pages-set(nonbody))
    assert not missing, f'Unreviewed PDF pages {missing}'
    assert body_pages | set(nonbody) == set(range(1, source[1]+1))
    toc, part = [], 'morphology'
    for p in sorted(metadata, key=lambda p: p['pdf_page']):
        if p['kind'] != 'contents':
            continue
        for line in p['visible_text'].splitlines():
            if line == '句法':
                part = 'syntax'
            match = re.fullmatch(r'§(\d+) (.+)（(\d+)）', line)
            if match:
                n, title, printed = match.groups()
                code = f'{part}.{int(n):03}'
                expected = int(printed)+20
                assert starts[code] == expected, f'TOC start {code}'
                toc.append(dict(code=code, toc_title=title,
                    chunk_title=chunks[code]['title'], pdf_page=expected))
    assert len(toc) == 356 and len({r['code'] for r in toc}) == 356
    counts = {s: sum(c['status'] == s for c in chunks.values())
              for s in ['ready', 'unresolved', 'incomplete']}
    report = dict(checked_at=now(), source_sha256=fingerprint,
        total_pdf_pages=source[1], body_pages=len(body_pages),
        nonbody_pages=len(nonbody), missing_pages=missing, chunks=counts,
        complete_section_boundaries=len(chunks), verified_batches=len(batches),
        verified_page_revisions=len(revisions),
        toc_matched_starts=len(toc), metadata_file_hashes=metadata_hashes,
        unresolved_notes=len(issues), unresolved_sections=len({i['code'] for i in issues}),
        limits='验证覆盖、来源和结构；不证明转写零错、语法正确或生成问答质量。')
    dump(work/'full_review_audit.json', report)
    dump(work/'unresolved_queue.json', dict(source_sha256=fingerprint, issues=issues))
    dump(work/'toc_verification.json', toc)
    lines = ['# 语法书未决项', '', report['limits'], '',
             f'共 {len(issues)} 条未决说明，影响 {report["unresolved_sections"]} 节。', '']
    for i in issues:
        lines.extend([f'## {i["title"]} · PDF {i["pdf_page"]}', '',
            i['note'], '', f'[原图]({i["image_path"]})；来源批次 `{i["batch_id"]}`。', ''])
    (work/'unresolved_queue.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
