"""Audit the aspect source, OCR coverage and immutable review evidence locally."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import aspect_reference as a
from grammar_rag import read_source, section_snapshot


def audit():
    result = a.status()
    errors = []
    fingerprint = result['source_sha256']
    chars = 0
    for number in range(1, result['total_pages'] + 1):
        path = a.WORK/'ocr'/f'p{number:04d}.json'
        if not path.exists():
            continue
        page = json.loads(path.read_text(encoding='utf-8'))
        if page['source_sha256'] != fingerprint or page['pdf_page'] != number or page['status'] != 'unreviewed':
            errors.append(f'OCR provenance/status mismatch: {number}')
        chars += len(page['text'])
    result['raw_ocr_characters'] = chars
    result['ready_sections'] = []
    result['excluded_sections'] = []
    with closing(sqlite3.connect(f'{a.DB.resolve().as_uri()}?mode=ro', uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute('BEGIN')
        source = read_source(conn)
        if source['sha256'] != fingerprint or source['title'] != a.TITLE:
            errors.append('Database source mismatch')
        batches = {}
        for row in conn.execute('SELECT * FROM batches'):
            path = a.WORK/'reviews'/f"{row['id']}.json"
            batch = json.loads(path.read_text(encoding='utf-8'))
            digest = hashlib.sha256(json.dumps(batch,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
            if digest != row['sha256']:
                errors.append(f"Batch hash mismatch: {row['id']}")
            a.core.validate_batch(batch, fingerprint, result['total_pages'])
            batches[row['id']] = batch
        result['batches'] = len(batches)
        for row in conn.execute('SELECT * FROM pages ORDER BY pdf_page'):
            number = row['pdf_page']
            page = json.loads(row['review_json'])
            digest = hashlib.sha256(row['review_json'].encode()).hexdigest()
            if digest != row['review_sha256']:
                errors.append(f'Page hash mismatch: {number}')
            candidates = [p for p in batches[row['batch_id']]['pages'] if p['pdf_page'] == number]
            if candidates != [page]:
                errors.append(f'Page not backed by immutable batch: {number}')
            image = a.WORK/'renders'/f'p{number:04d}.png'
            if not image.exists() or a.core.file_sha256(image) != page.get('render_sha256'):
                errors.append(f'Render hash mismatch: {number}')
        for row in conn.execute('SELECT * FROM chunks ORDER BY code'):
            if row['status'] == 'ready':
                item = section_snapshot(conn,row['code'],source)
                result['ready_sections'].append({k:item[k] for k in ('code','title','pdf_pages','printed_pages','body_sha256')})
            else:
                result['excluded_sections'].append(dict(code=row['code'],status=row['status'],pdf_pages=json.loads(row['pdf_pages']),notes=json.loads(row['notes'])))
        result['foreign_key_errors'] = len(list(conn.execute('PRAGMA foreign_key_check')))
    result.update(created_at=a.core.now(),errors=errors,
        database_sha256=a.core.file_sha256(a.DB),
        next_review_pdf_page=max(result.get('reviewed_pages') or [20])+1,
        limits='Checks prove provenance/coverage and section boundaries, not textual accuracy, independent expert review or generated-answer correctness.')
    if errors or result['foreign_key_errors'] or result['integrity'] != 'ok':
        raise ValueError(json.dumps(result,ensure_ascii=False))
    a.core.dump(a.WORK/'checkpoint.json',result)
    return result


if __name__ == '__main__':
    result=audit()
    print(json.dumps({k:v for k,v in result.items() if k not in ('reviewed_pages','ready_sections','excluded_sections')},ensure_ascii=False,indent=2))
