"""Replay the documented correction to batch 004, preserving its original evidence."""
import argparse
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from import_vocabulary_learning import DEFAULT_DB, ROOT, locate

SOURCE = 'https://gramota.ru/poisk?mode=slovari&query=%D0%BF%D0%BE%D0%BB%D0%B2%D0%B5%D0%BA%D0%B0'


def correct(db_path, apply=False, backup_dir=None):
    catalog = json.loads((ROOT / 'data/review_samples/learning_batch_004_catalog.json').read_text(encoding='utf-8'))
    item = next(row for row in catalog['records'] if row['id'] == 4315)
    old = dict(canonical_word=item['canonical'], accent=item['accent'], part=item['part'],
               core_meaning_zh=item['meaning'], aspect_partner=item['perfective'], note=item['note'],
               stage=item['stage'], original_json=json.dumps(item['original'], ensure_ascii=False, sort_keys=True),
               review_method=item['method'], evidence_json=json.dumps(item['evidence'], ensure_ascii=False))
    new = dict(old, part='名词·阳性（亦有复数用法）',
               note='数量表达：半个世纪。不能根据过去时谓语的中性形式推断名词性。',
               review_method=old['review_method'] + ' 2026-09-08更正：据Gramota词典撤销原中性标注。',
               evidence_json=json.dumps([SOURCE, '词典标注м. и мн.；正字与正音词典主重音在ве。'], ensure_ascii=False))
    uri = db_path.resolve().as_uri() + ('?mode=rw' if apply else '?mode=ro')
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        word_id = locate(conn, item)

        def state():
            row = conn.execute('SELECT * FROM vocabulary_learning_annotations WHERE vocabulary_item_id=?', (word_id,)).fetchone()
            if row is None:
                raise ValueError('先导入batch004；不会绕过原值审核创建标注。')
            if all(row[k] == v for k, v in new.items()):
                return 'already_corrected'
            if any(row[k] != v for k, v in old.items()):
                raise ValueError('已有后续标注，停止覆盖。')
            return 'pending'

        result = state()
        if not apply or result == 'already_corrected':
            return dict(state=result, database_written=False)
        directory = backup_dir or ROOT / 'data/processed/backups'
        directory.mkdir(parents=True, exist_ok=True)
        backup_path = directory / f'learning_polvieka_{datetime.now():%Y%m%d_%H%M%S_%f}.sqlite'
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
                raise ValueError('数据库完整性检查失败')
        return dict(state='corrected', database_written=True, backup=str(backup_path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(correct(args.db, args.apply), ensure_ascii=False))
