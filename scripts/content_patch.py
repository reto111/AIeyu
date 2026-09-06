"""Source-keyed content updates with preconditions; never copy user databases."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from contextlib import contextmanager, closing
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / 'database/content_patches/multimodal_20260903.json'


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


@contextmanager
def connect(path, writable=False):
    con = sqlite3.connect(Path(path).resolve().as_uri() + ('?mode=rw' if writable else '?mode=ro'), uri=True)
    try:
        with con:
            yield con
    finally:
        con.close()


def locate(con, key):
    rows = con.execute('''SELECT q.id, q.passage_id FROM questions q
        JOIN exam_systems e ON e.id=q.exam_system_id
        WHERE e.code=? AND q.source_year=? AND q.source_question_number=?
        AND q.content_origin='past_exam_original' ''', key).fetchall()
    if len(rows) != 1:
        raise ValueError(f'Source key must match exactly once: {key}; matches={len(rows)}')
    return rows[0]


def field_target(con, item):
    qid, passage_id = locate(con, item['key'])
    field = item['field']
    if field in ('stem', 'correct_answer', 'source_page'):
        return 'questions', field, 'id=?', (qid,)
    if field.startswith('option:') and field[7:] in ('A', 'B', 'C', 'D'):
        return 'question_options', 'option_text', 'question_id=? AND option_key=?', (qid, field[7:])
    if field == 'body' and passage_id is not None:
        # Check that this passage belongs to the same group, not a wrong split.
        members = [list(r) for r in con.execute('''SELECT e.code,q.source_year,q.source_question_number
            FROM questions q JOIN exam_systems e ON e.id=q.exam_system_id
            WHERE q.passage_id=? ORDER BY e.code,q.source_year,q.source_question_number''', (passage_id,))]
        if members != item['members']:
            raise ValueError(f'Passage membership changed: {item["key"]}')
        return 'passages', 'body', 'id=?', (passage_id,)
    raise ValueError(f'Unsupported field or missing passage: {field}')


def inspect(con, manifest):
    changes, conflicts, skipped = [], [], 0
    for item in manifest['items']:
        try:
            table, column, where, args = field_target(con, item)
            rows = con.execute(f'SELECT {column} FROM {table} WHERE {where}', args).fetchall()
            if len(rows) != 1:
                raise ValueError('Field must match exactly once')
            value = rows[0][0]
            if value == item['new']:
                skipped += 1
            elif digest(value) == item['old_hash']:
                changes.append((item, table, column, where, args, value))
            else:
                conflicts.append({'key': item['key'], 'field': item['field'], 'reason': 'unexpected_current_value'})
        except ValueError as exc:
            conflicts.append({'key': item['key'], 'field': item['field'], 'reason': str(exc)})
    return changes, conflicts, skipped


def apply_patch(db, manifest_path=DEFAULT_MANIFEST, apply=False, output_dir=None):
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 1:
        raise ValueError('Unsupported manifest version')
    output_dir = Path(output_dir or Path(db).resolve().parent / 'content_update_reports')
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    report = {'patch_id': manifest['patch_id'], 'manifest_hash': digest(manifest),
              'mode': 'apply' if apply else 'preview', 'backup': None}
    with connect(db) as reader:
        initial_changes, conflicts, _ = inspect(reader, manifest)
        if apply and initial_changes and not conflicts:
            backup = output_dir / f'before_{stamp}.sqlite'
            with closing(sqlite3.connect(backup)) as dest:
                reader.backup(dest)
            report['backup'] = str(backup)
    with connect(db, writable=apply) as con:
        if apply:
            con.execute('BEGIN IMMEDIATE')
        changes, conflicts, skipped = inspect(con, manifest)
        report.update(changed_fields=len(changes), skipped_fields=skipped, conflicts=conflicts)
        if apply and not conflicts:
            if changes and report['backup'] is None:
                raise ValueError('Content changed after preview; retry with the service stopped to create a backup')
            for item, table, column, where, args, old in changes:
                con.execute(f'UPDATE {table} SET {column}=?, updated_at=CURRENT_TIMESTAMP WHERE {where}',
                            (item['new'], *args))
            if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Database integrity check failed; transaction rolled back')
            # Append-only update receipt; historical review decisions are untouched.
            if changes:
                con.execute('''CREATE TABLE IF NOT EXISTS content_patch_events (
                    id INTEGER PRIMARY KEY, patch_id TEXT NOT NULL, manifest_hash TEXT NOT NULL,
                    changes_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
                con.execute('INSERT INTO content_patch_events(patch_id,manifest_hash,changes_json) VALUES(?,?,?)',
                            (manifest['patch_id'], digest(manifest), json.dumps([
                                {'key': x[0]['key'], 'field': x[0]['field'], 'old': x[5], 'new': x[0]['new']}
                                for x in changes], ensure_ascii=False)))
            con.commit()
        elif apply:
            con.rollback()
    report['status'] = 'conflict' if conflicts else ('applied' if apply else 'preview_ready')
    report_path = output_dir / f'{stamp}_{report["mode"]}.json'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    report['report_path'] = str(report_path)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default=str(ROOT / 'database/russian_ai_tutor.sqlite'))
    parser.add_argument('--manifest', default=str(DEFAULT_MANIFEST))
    parser.add_argument('--output-dir')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    result = apply_patch(args.db, args.manifest, args.apply, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(2 if result['conflicts'] else 0)


if __name__ == '__main__':
    main()
