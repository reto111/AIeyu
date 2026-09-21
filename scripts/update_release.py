"""Validate the complete release on a database copy before applying it."""
import argparse
import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from archive_vocabulary_headers import archive
from import_vocabulary_learning import apply_catalog, DEFAULT_DB, ROOT

PATCH = ROOT / 'data/review_samples/vocabulary_release_catalog.json'


def update(db, patch, apply=False):
    if not db.is_file() or not patch.is_file():
        raise ValueError('Database or release catalog missing; no empty database will be created.')
    with tempfile.TemporaryDirectory(prefix='aieyu_release_') as folder:
        copy = Path(folder) / 'preview.sqlite'
        with closing(sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True)) as source:
            with closing(sqlite3.connect(copy)) as target:
                source.backup(target)
        before = snapshot(copy)
        preview = apply_catalog(copy, patch, True, Path(folder) / 'backups')
        archives = archive(copy, True, Path(folder) / 'backups')
        if snapshot(copy) != before:
            raise ValueError('Unexpected changes outside vocabulary annotations/archive status')
    if not apply:
        return dict(validated=True, new_annotations=preview['inserted'], existing_annotations=preview['skipped'],
                    archives=archives.get('changed', 0), database_written=False)
    result = apply_catalog(db.resolve(), patch, True)
    result['archives'] = archive(db.resolve(), True)
    return result


def snapshot(db):
    # Compare all rows, not just counts, outside the two intended content tables.
    with closing(sqlite3.connect(db)) as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                  if r[0] not in ('vocabulary_learning_annotations', 'vocabulary_items', 'user_vocabulary_settings')]
        return {t: conn.execute('SELECT * FROM "' + t.replace('"', '""') + '" ORDER BY rowid').fetchall() for t in tables}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--patch', type=Path, default=PATCH)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(update(args.db, args.patch, args.apply), ensure_ascii=False))
