"""Reconstruct only the historical patch fields from verified local snapshots."""
import argparse
import json
from pathlib import Path

from content_patch import ROOT, DEFAULT_MANIFEST, connect, digest, locate
from apply_multimodal_question_fixes import FIXES, PASSAGE_REPLACEMENTS


def build(baseline, target, output):
    items = []
    with connect(baseline) as before, connect(target) as after:
        for key, fix in FIXES.items():
            old_id, _ = locate(before, key)
            new_id, _ = locate(after, key)
            for field in ('stem', 'correct_answer', 'source_page'):
                if field not in fix:
                    continue
                old = before.execute(f'SELECT {field} FROM questions WHERE id=?', (old_id,)).fetchone()[0]
                new = after.execute(f'SELECT {field} FROM questions WHERE id=?', (new_id,)).fetchone()[0]
                if new != fix[field]:
                    raise ValueError(f'Target differs from historical fix: {key} {field}')
                if old != new:
                    items.append({'key': key, 'field': field, 'old_hash': digest(old), 'new': new,
                                  'evidence': 'historical_source_fix', 'note': fix['note']})
            for option, expected in fix.get('options', {}).items():
                sql = 'SELECT option_text FROM question_options WHERE question_id=? AND option_key=?'
                old = before.execute(sql, (old_id, option)).fetchone()[0]
                new = after.execute(sql, (new_id, option)).fetchone()[0]
                if new != expected:
                    raise ValueError(f'Target differs from historical option fix: {key} {option}')
                if old != new:
                    items.append({'key': key, 'field': 'option:' + option, 'old_hash': digest(old),
                                  'new': new, 'evidence': 'historical_source_fix', 'note': fix['note']})
        for key in PASSAGE_REPLACEMENTS:
            _, old_id = locate(before, key)
            _, new_id = locate(after, key)
            old = before.execute('SELECT body FROM passages WHERE id=?', (old_id,)).fetchone()[0]
            new = after.execute('SELECT body FROM passages WHERE id=?', (new_id,)).fetchone()[0]
            members = [list(r) for r in after.execute('''SELECT e.code,q.source_year,q.source_question_number
                FROM questions q JOIN exam_systems e ON e.id=q.exam_system_id
                WHERE q.passage_id=? ORDER BY e.code,q.source_year,q.source_question_number''', (new_id,))]
            if old != new:
                items.append({'key': key, 'field': 'body', 'old_hash': digest(old), 'new': new,
                              'members': members, 'evidence': 'historical_passage_fix'})
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'schema_version': 1, 'patch_id': 'multimodal_20260903_v1',
        'baseline': Path(baseline).name, 'items': items}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Created {output}: {len(items)} fields; no student data exported')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--output', default=str(DEFAULT_MANIFEST))
    args = parser.parse_args()
    build(args.baseline, args.target, args.output)
