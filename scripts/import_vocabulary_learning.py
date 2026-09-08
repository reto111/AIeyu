"""Prepare/replay reviewed annotations without replacing student or source records."""
import argparse
import json
import re
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from build_vocabulary_sample import SOURCES
from vocabulary_learning import ensure_learning_tables

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / 'data/review_samples/learning_catalog.json'
DEFAULT_DB = ROOT / 'database/russian_ai_tutor.sqlite'
FIELDS = ('word', 'part_of_speech', 'meaning_zh', 'source_page', 'source_line')


def check_accent(text):
    if not re.fullmatch('[А-Яа-яЁё\u0301-]+', text):
        raise ValueError(f'不支持的重音形式: {text}')
    pieces = text.lower().split('-')
    for index, piece in enumerate(pieces):
        count = sum(c in 'аеёиоуыэюя' for c in piece)
        unstressed_suffix = index > 0 and index == len(pieces)-1 and piece in ('либо','нибудь','то')
        if piece.count('\u0301') > 1 or (count > 1 and '\u0301' not in piece and 'ё' not in piece and not unstressed_suffix):
            raise ValueError(f'缺失或重复重音: {text}')
        if '\u0301' in piece and (piece.index('\u0301') == 0 or piece[piece.index('\u0301')-1] not in 'аеёиоуыэюя'):
            raise ValueError(f'重音不在元音: {text}')


def prepare(db_path, output=PATCH, review_files=None):
    if output.exists():
        raise ValueError('已有原值快照，禁止重新覆盖。新增审核使用新批次文件。')
    records = []
    with closing(sqlite3.connect(db_path.as_uri() + '?mode=ro', uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        for filename in (review_files or ('beginner_100.json', 'learning_batch_001.json')):
            data = json.loads((ROOT / 'data/review_samples' / filename).read_text(encoding='utf-8'))
            for values in data['rows']:
                item = dict(zip(data['columns'], values, strict=True))
                check_accent(item['accent'])
                if item['perfective']:
                    check_accent(item['perfective'])
                old = conn.execute('''SELECT v.*, e.code AS exam, l.code AS level
                    FROM vocabulary_items v JOIN exam_systems e ON e.id=v.exam_system_id
                    JOIN exam_levels l ON l.id=v.level_id WHERE v.id=? AND v.review_status='approved' ''',
                    (item['id'],)).fetchone()
                if not old:
                    raise ValueError(f"词条不在正式库: {item['id']}")
                canonical = item['accent'].replace('\u0301','')
                explicit_correction = data.get('word_corrections', {}).get(str(item['id']))
                allowed_correction = explicit_correction == [old['word'], canonical]
                if canonical != old['word'] and not allowed_correction and not (old['word']=='идёя' and canonical=='идея'):
                    raise ValueError(f'未确认词头变更: {canonical}')
                item['original'] = {key: old[key] for key in FIELDS}
                item.update(exam=old['exam'], level=old['level'], canonical=canonical,
                            stage=item.get('stage', 2 if item['id'] in (8449,7813,10073,8691,7669) else 1),
                            method=data.get('method', '模型逐项审核'),
                            evidence=data.get('sources', {}).get(str(item['id']), SOURCES.get(item['id'], [])))
                if item['id'] == 8560:
                    item['note'] = '已核原书 PDF 第117页（印刷页110）：粥、稀饭；转义糊里糊涂。咳嗽属于紧邻的 кашель。'
                    item['evidence'] = ['data/words/tem4_russian_words.pdf#page=117', '本次逐项视觉核对词头、重音、阴性及中文；另有 Gramota 词典抽核']
                records.append(item)
    if len({r['id'] for r in records}) != len(records):
        raise ValueError('批次 ID 重复')
    output.write_text(json.dumps(dict(schema_version=1, records=records), ensure_ascii=False, indent=2), encoding='utf-8')
    return {'prepared': len(records), 'path': str(output)}


def locate(conn, item):
    rows = conn.execute('''SELECT v.* FROM vocabulary_items v
        JOIN exam_systems e ON e.id=v.exam_system_id JOIN exam_levels l ON l.id=v.level_id
        WHERE e.code=? AND l.code=? AND v.word=? AND v.part_of_speech IS ?
          AND v.source_page IS ? AND v.source_line IS ?''',
        (item['exam'], item['level'], item['original']['word'], item['original']['part_of_speech'],
         item['original']['source_page'], item['original']['source_line'])).fetchall()
    if len(rows) != 1 or rows[0]['review_status'] != 'approved':
        raise ValueError(f"来源键缺失、非唯一或未批准: {item['id']} {item['original']['word']}")
    if any(rows[0][key] != item['original'][key] for key in FIELDS):
        raise ValueError(f"原值已变化，需重核: {item['id']} {item['original']['word']}")
    return rows[0]['id']


def apply_catalog(db_path, patch_path=PATCH, apply=False, backup_dir=None):
    records = json.loads(patch_path.read_text(encoding='utf-8'))['records']
    with closing(sqlite3.connect(db_path.as_uri()+'?mode=ro', uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        for item in records:
            locate(conn, item)
            check_accent(item['accent'])
            if item['stage'] not in range(1,5) or not item['meaning'].strip():
                raise ValueError('无效级别或空释义')
    if not apply:
        return {'validated': len(records), 'database_written': False}
    backup_dir = backup_dir or ROOT / 'data/processed/backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f'vocabulary_learning_{datetime.now():%Y%m%d_%H%M%S_%f}.sqlite'
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        with closing(sqlite3.connect(backup_path)) as backup:
            conn.backup(backup)
        ensure_learning_tables(conn)
        conn.execute('BEGIN IMMEDIATE')
        inserted = skipped = 0
        try:
            for item in records:
                word_id = locate(conn, item)
                values = dict(canonical_word=item['canonical'], accent=item['accent'], part=item['part'],
                              core_meaning_zh=item['meaning'], aspect_partner=item['perfective'], note=item['note'],
                              stage=item['stage'], original_json=json.dumps(item['original'], ensure_ascii=False, sort_keys=True),
                              review_method=item['method'], evidence_json=json.dumps(item['evidence'], ensure_ascii=False))
                existing = conn.execute('SELECT * FROM vocabulary_learning_annotations WHERE vocabulary_item_id=?', (word_id,)).fetchone()
                if existing:
                    if any(existing[k] != v for k,v in values.items()):
                        raise ValueError(f'已有不同审核内容，不能覆盖: {word_id}')
                    skipped += 1
                    continue
                columns = ','.join(values)
                placeholders = ','.join('?' for _ in values)
                conn.execute(f'INSERT INTO vocabulary_learning_annotations(vocabulary_item_id,{columns}) VALUES (?,{placeholders})',
                             (word_id, *values.values()))
                inserted += 1
            if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('数据库完整性检查未通过')
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return dict(inserted=inserted, skipped=skipped, backup=str(backup_path), database_written=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--patch', type=Path, default=PATCH)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--review-file', action='append', help='已逐词填写的审核批次文件名；只用于 --prepare')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error('数据库不存在；不会创建空库。')
    result = prepare(args.db.resolve(), args.patch, args.review_file) if args.prepare else apply_catalog(args.db.resolve(), args.patch, args.apply)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
