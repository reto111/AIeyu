"""Fix the verified Chinese OCR typo only; pronunciation remains unresolved."""
import argparse
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from import_vocabulary_learning import DEFAULT_DB, ROOT

SOURCE = 'data/words/tem8_russian_words.pdf#page=120'
OLD = '中国大民解放军'
NEW = '中国人民解放军'


def correct(db_path, apply=False, backup_dir=None):
    uri = db_path.resolve().as_uri() + ('?mode=rw' if apply else '?mode=ro')
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        conn.row_factory = sqlite3.Row

        def state():
            rows = conn.execute('''SELECT v.* FROM vocabulary_items v
                JOIN exam_systems e ON e.id=v.exam_system_id
                JOIN exam_levels l ON l.id=v.level_id
                WHERE e.code='TEM8_RU' AND l.code='TEM8' AND v.word='НОАК'
                  AND v.part_of_speech IS NULL AND v.source_page=120 AND v.source_line='9'
                ''').fetchall()
            if len(rows) != 1 or rows[0]['review_status'] != 'approved':
                raise ValueError('Source missing, ambiguous or not approved')
            row = rows[0]
            if row['meaning_zh'] == NEW:
                return row['id'], 'already_corrected'
            if row['meaning_zh'] != OLD:
                raise ValueError('Meaning changed; refusing overwrite')
            if conn.execute('SELECT 1 FROM vocabulary_learning_annotations WHERE vocabulary_item_id=?', (row['id'],)).fetchone():
                raise ValueError('Annotation exists; re-review before changing its baseline')
            return row['id'], 'pending'

        word_id, status = state()
        if not apply or status == 'already_corrected':
            return dict(state=status, database_written=False)
        directory = backup_dir or ROOT / 'data/processed/backups'
        directory.mkdir(parents=True, exist_ok=True)
        backup = directory / f'vocabulary_noak_{datetime.now():%Y%m%d_%H%M%S_%f}.sqlite'
        with closing(sqlite3.connect(backup)) as target:
            conn.backup(target)
        with conn:
            conn.execute('BEGIN IMMEDIATE')
            word_id, status = state()
            if status == 'pending':
                conn.execute('UPDATE vocabulary_items SET meaning_zh=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', (NEW, word_id))
            if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Integrity check failed')
        return dict(state='corrected', database_written=True, backup=str(backup))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(correct(args.db, args.apply), ensure_ascii=False))
