"""Correct a mixed-alphabet typo in batch144's explanatory note only."""
import argparse
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from import_vocabulary_learning import ROOT, DEFAULT_DB, locate


def correct(db, apply=False):
    catalog = json.loads((ROOT / 'data/review_samples/learning_batch_144_catalog.json').read_text(encoding='utf-8'))
    item = next(r for r in catalog['records'] if r['id'] == 10636)
    old = dict(canonical_word=item['canonical'], accent=item['accent'], part=item['part'],
               core_meaning_zh=item['meaning'], aspect_partner=item['perfective'], note=item['note'],
               stage=item['stage'], original_json=json.dumps(item['original'], ensure_ascii=False, sort_keys=True),
               review_method=item['method'], evidence_json=json.dumps(item['evidence'], ensure_ascii=False))
    new = dict(old, note='原页列出未完成体умыва́ться及完成体умы́ться；本记录保留完成体词头，关联未完成体。')
    with closing(sqlite3.connect(db.resolve().as_uri() + ('?mode=rw' if apply else '?mode=ro'), uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        def state():
            word_id = locate(conn, item)
            row = conn.execute('SELECT * FROM vocabulary_learning_annotations WHERE vocabulary_item_id=?', (word_id,)).fetchone()
            if row and all(row[k] == v for k, v in new.items()):
                return word_id, 'already_corrected'
            if not row or any(row[k] != v for k, v in old.items()):
                raise ValueError('Annotation changed; refusing overwrite')
            return word_id, 'pending'
        word_id, status = state()
        if not apply or status == 'already_corrected':
            return dict(state=status, database_written=False)
        backup = ROOT / 'data/processed/backups' / f'learning_note_{datetime.now():%Y%m%d_%H%M%S_%f}.sqlite'
        with closing(sqlite3.connect(backup)) as target:
            conn.backup(target)
        with conn:
            conn.execute('BEGIN IMMEDIATE')
            word_id, status = state()
            if status == 'pending':
                conn.execute('UPDATE vocabulary_learning_annotations SET note=?, reviewed_at=CURRENT_TIMESTAMP WHERE vocabulary_item_id=?', (new['note'], word_id))
        return dict(state='corrected', backup=str(backup), database_written=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(correct(args.db, args.apply), ensure_ascii=False))
