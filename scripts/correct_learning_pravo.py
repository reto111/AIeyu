"""Append the PDF220 plural sense without rewriting batch111 history."""
import argparse
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from import_vocabulary_learning import DEFAULT_DB, ROOT, locate


def correct(db_path, apply=False, backup_dir=None):
    catalog = json.loads((ROOT / 'data/review_samples/learning_batch_111_catalog.json').read_text(encoding='utf-8'))
    item = next(row for row in catalog['records'] if row['id'] == 9650)
    old = dict(canonical_word=item['canonical'], accent=item['accent'], part=item['part'],
               core_meaning_zh=item['meaning'], aspect_partner=item['perfective'], note=item['note'],
               stage=item['stage'], original_json=json.dumps(item['original'], ensure_ascii=False, sort_keys=True),
               review_method=item['method'], evidence_json=json.dumps(item['evidence'], ensure_ascii=False))
    new = dict(old, note=old['note'] + ' 复数права́在口语中可指驾驶证，完整说法води́тельские права́。',
               review_method=old['review_method'] + ' 2026-09-17跨页复查追加PDF220驾驶证义说明。')
    uri = db_path.resolve().as_uri() + ('?mode=rw' if apply else '?mode=ro')
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        word_id = locate(conn, item)

        def state():
            row = conn.execute('SELECT * FROM vocabulary_learning_annotations WHERE vocabulary_item_id=?', (word_id,)).fetchone()
            if row is None:
                raise ValueError('Import batch111 first.')
            if all(row[k] == v for k, v in new.items()):
                return 'already_corrected'
            if any(row[k] != v for k, v in old.items()):
                raise ValueError('Later annotation exists; refusing overwrite.')
            return 'pending'

        result = state()
        if not apply or result == 'already_corrected':
            return dict(state=result, database_written=False)
        directory = backup_dir or ROOT / 'data/processed/backups'
        directory.mkdir(parents=True, exist_ok=True)
        backup_path = directory / f'learning_pravo_{datetime.now():%Y%m%d_%H%M%S_%f}.sqlite'
        with closing(sqlite3.connect(backup_path)) as backup:
            conn.backup(backup)
        with conn:
            conn.execute('BEGIN IMMEDIATE')
            locate(conn, item)
            if state() != 'pending':
                return dict(state='already_corrected', database_written=False)
            conn.execute('UPDATE vocabulary_learning_annotations SET ' + ','.join(k+'=?' for k in new) +
                         ', reviewed_at=CURRENT_TIMESTAMP WHERE vocabulary_item_id=?', (*new.values(), word_id))
            if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Integrity check failed.')
        return dict(state='corrected', database_written=True, backup=str(backup_path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(correct(args.db, args.apply), ensure_ascii=False))
