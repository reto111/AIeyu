"""Archive visually confirmed PDF header artifacts, retaining IDs and history."""
import argparse
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from import_vocabulary_learning import DEFAULT_DB, ROOT

MANIFEST = ROOT / 'data/review_samples/learning_header_archives.json'


def find(conn, item):
    rows = conn.execute('''SELECT v.* FROM vocabulary_items v
        JOIN exam_systems e ON e.id=v.exam_system_id JOIN exam_levels l ON l.id=v.level_id
        WHERE e.code=? AND l.code=? AND v.word=? AND v.part_of_speech IS ?
        AND v.source_page=? AND v.source_line=?''',
        (item['exam'], item['level'], item['word'], item['part'], item['page'], item['line'])).fetchall()
    if len(rows) != 1 or rows[0]['meaning_zh'] != item['meaning']:
        raise ValueError(f"来源或原值已变化，不能归档：{item['id']}")
    if rows[0]['review_status'] not in ('approved', 'archived'):
        raise ValueError(f"审核状态已有后续调整，停止：{item['id']}")
    return rows[0]


def archive(db_path, apply=False, backup_dir=None):
    items = json.loads(MANIFEST.read_text(encoding='utf-8'))['records']
    with closing(sqlite3.connect(db_path.resolve().as_uri() + ('?mode=rw' if apply else '?mode=ro'), uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        rows = [find(conn, item) for item in items]
        count = sum(row['review_status'] == 'approved' for row in rows)
        if not apply or not count:
            return dict(state='pending' if count else 'archived', pending=count, database_written=False)
        directory = backup_dir or ROOT / 'data/processed/backups'
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f'word_headers_{datetime.now():%Y%m%d_%H%M%S_%f}.sqlite'
        with closing(sqlite3.connect(path)) as target:
            conn.backup(target)
        with conn:
            conn.execute('BEGIN IMMEDIATE')
            rows = [find(conn, item) for item in items]
            changed = 0
            for row in rows:
                if row['review_status'] == 'approved':
                    conn.execute("UPDATE vocabulary_items SET review_status='archived', updated_at=CURRENT_TIMESTAMP WHERE id=?", (row['id'],))
                    changed += 1
        return dict(state='archived', changed=changed, database_written=bool(changed), backup=str(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(archive(args.db, args.apply), ensure_ascii=False))
