"""Export conservative historical evidence coverage, not a correctness score."""
import argparse
import csv
import json
import sqlite3
from pathlib import Path

from content_patch import ROOT, DEFAULT_MANIFEST, connect, digest


def export(db, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding='utf-8'))
    fixes = {}
    for item in manifest['items']:
        fixes.setdefault(tuple(item['key']), []).append(item)
    issues = {}
    audit = ROOT / 'data/processed/question_quality/question_quality_audit.csv'
    if audit.exists():
        with audit.open(encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                issues.setdefault(int(row['question_id']), set()).add(row['issue_code'])
    rows, passages = [], []
    with connect(db) as con:
        con.row_factory = sqlite3.Row
        for q in con.execute('''SELECT q.*,e.code AS exam FROM questions q
            JOIN exam_systems e ON e.id=q.exam_system_id ORDER BY e.code,q.source_year,q.id'''):
            key = (q['exam'], q['source_year'], q['source_question_number'])
            options = dict(con.execute('SELECT option_key,option_text FROM question_options WHERE question_id=?', (q['id'],)))
            evidence = [x for x in fixes.get(key, []) if x['field'] != 'body'] if q['content_origin'] == 'past_exam_original' else []
            def current(item):
                return options.get(item['field'][7:]) if item['field'].startswith('option:') else q[item['field']]
            matched = all(current(x) == x['new'] for x in evidence)
            rows.append({'question_id': q['id'], 'exam': q['exam'], 'year': q['source_year'],
                'number': q['source_question_number'], 'source_page': q['source_page'],
                'origin': q['content_origin'], 'review_status': q['review_status'], 'usage': q['source_usage'],
                'passage_id': q['passage_id'], 'historical_fixed_fields': '|'.join(x['field'] for x in evidence),
                'evidence_status': ('historical_field_fixes_match' if matched else 'changed_since_patch') if evidence else 'no_field_patch_evidence',
                'full_visual_review': 'not_established_by_this_manifest',
                'prior_rule_flags': '|'.join(sorted(issues.get(q['id'], []))),
                'content_hash': digest([q['stem'], options, q['correct_answer']])})
        for p in con.execute('SELECT id,title,body,source_page_start,source_page_end FROM passages ORDER BY id'):
            members = [list(r) for r in con.execute('''SELECT e.code,q.source_year,q.source_question_number
                FROM questions q JOIN exam_systems e ON e.id=q.exam_system_id WHERE q.passage_id=?
                ORDER BY e.code,q.source_year,q.source_question_number''', (p['id'],))]
            candidates = [x for x in manifest['items'] if x['field'] == 'body' and x['members'] == members]
            passages.append({'passage_id': p['id'], 'title': p['title'], 'page_start': p['source_page_start'],
                'page_end': p['source_page_end'], 'member_keys': json.dumps(members, ensure_ascii=False),
                'evidence_status': ('historical_body_fix_matches' if p['body'] == candidates[0]['new'] else 'changed_since_patch') if candidates else 'no_body_patch_evidence',
                'body_hash': digest(p['body'])})
    for name, data in [('questions', rows), ('passages', passages)]:
        with (out / f'{name}.csv').open('w', encoding='utf-8-sig', newline='') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=list(data[0]))
                writer.writeheader()
                writer.writerows(data)
    summary = {'questions': len(rows), 'passages': len(passages),
        'questions_with_field_patch_evidence': sum(bool(r['historical_fixed_fields']) for r in rows),
        'passages_with_body_patch_evidence': sum(r['evidence_status'] != 'no_body_patch_evidence' for r in passages),
        'prior_audit_file': str(audit), 'prior_audit_rerun': False,
        'note': 'Historical field/body patch evidence only; no new visual review or vocabulary review performed.'}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default=str(ROOT / 'database/russian_ai_tutor.sqlite'))
    parser.add_argument('--out', default=str(ROOT / 'data/processed/review_coverage'))
    args = parser.parse_args()
    print(json.dumps(export(args.db, args.out), ensure_ascii=False, indent=2))
