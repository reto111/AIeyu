"""Export conservative historical evidence coverage, not a correctness score."""
import argparse
import csv
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from content_patch import ROOT, DEFAULT_MANIFEST, connect, digest


def review_state(key, content_hash, records):
    """Only the latest recorded decision can describe the current content."""
    matches = [r for r in records if r['key'] == key]
    if not matches:
        return '未登记', None
    record = matches[-1]
    if record['content_hash'] != content_hash:
        return '内容已变化，需复核', record
    return record['verdict'], record


def load_records(path):
    if not path.exists():
        return []
    records = []
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        required = ('key', 'content_hash', 'fields', 'verdict', 'reviewer', 'method', 'source', 'reviewed_at')
        if any(not record.get(field) for field in required):
            raise ValueError(f'{path}:{number}: incomplete review evidence')
        if not isinstance(record['fields'], list) or not all(isinstance(f, str) for f in record['fields']):
            raise ValueError(f'{path}:{number}: fields must be a list of field names')
        if not isinstance(record['key'], list):
            raise ValueError(f'{path}:{number}: key must be a list')
        if record['verdict'] not in ('已核对', '待确认', '弃用'):
            raise ValueError(f'{path}:{number}: unsupported verdict')
        records.append(record)
    return records


def export(db, out, records_path=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    records_path = Path(records_path) if records_path else ROOT / 'data/review_records/content_reviews.jsonl'
    records = load_records(records_path)
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
                'content_hash': digest([q['stem'], options, q['correct_answer'], q['passage_id']]),
                'stem': q['stem'], 'options': json.dumps(options, ensure_ascii=False),
                'answer': q['correct_answer']})
            record_key = ['question', *key, q['content_origin']]
            if q['content_origin'] != 'past_exam_original':
                record_key.append(q['id'])
            rows[-1]['record_key'] = json.dumps(record_key, ensure_ascii=False)
            state, record = review_state(record_key, rows[-1]['content_hash'], records)
            rows[-1].update({'record_status': state, 'reviewed_fields': '|'.join(record['fields']) if record else '',
                'reviewer': record['reviewer'] if record else '', 'method': record['method'] if record else '',
                'evidence_source': record['source'] if record else '',
                'reviewed_at': record['reviewed_at'] if record else ''})
        for p in con.execute('SELECT id,title,body,source_page_start,source_page_end FROM passages ORDER BY id'):
            members = [list(r) for r in con.execute('''SELECT e.code,q.source_year,q.source_question_number
                FROM questions q JOIN exam_systems e ON e.id=q.exam_system_id WHERE q.passage_id=?
                ORDER BY e.code,q.source_year,q.source_question_number''', (p['id'],))]
            candidates = [x for x in manifest['items'] if x['field'] == 'body' and x['members'] == members]
            passages.append({'passage_id': p['id'], 'title': p['title'], 'page_start': p['source_page_start'],
                'page_end': p['source_page_end'], 'member_keys': json.dumps(members, ensure_ascii=False),
                'evidence_status': ('historical_body_fix_matches' if p['body'] == candidates[0]['new'] else 'changed_since_patch') if candidates else 'no_body_patch_evidence',
                'body_hash': digest(p['body'])})
            record_key = ['passage', members] if members else ['passage_without_questions', p['id']]
            passages[-1]['record_key'] = json.dumps(record_key, ensure_ascii=False)
            state, record = review_state(record_key, passages[-1]['body_hash'], records)
            passages[-1].update({'record_status': state, 'reviewed_fields': '|'.join(record['fields']) if record else '',
                'evidence_source': record['source'] if record else '',
                'reviewer': record['reviewer'] if record else '', 'method': record['method'] if record else '',
                'reviewed_at': record['reviewed_at'] if record else ''})
    for name, data in [('questions', rows), ('passages', passages)]:
        with (out / f'{name}.csv').open('w', encoding='utf-8-sig', newline='') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=list(data[0]))
                writer.writeheader()
                writer.writerows(data)
    summary = {'questions': len(rows), 'passages': len(passages),
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'review_records_file': str(records_path), 'review_records': len(records),
        'question_record_statuses': dict(Counter(r['record_status'] for r in rows)),
        'passage_record_statuses': dict(Counter(r['record_status'] for r in passages)),
        'questions_with_field_patch_evidence': sum(bool(r['historical_fixed_fields']) for r in rows),
        'passages_with_body_patch_evidence': sum(r['evidence_status'] != 'no_body_patch_evidence' for r in passages),
        'prior_audit_file': str(audit), 'prior_audit_rerun': False,
        'note': 'Historical field/body patch evidence only; no new visual review or vocabulary review performed.'}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    report = ['# 内容审核覆盖概览', '', f"导出时间：{summary['exported_at']}", '',
        '记录整理不代表重新审核。历史修正只证明指定字段曾被修正；没有登记不等于内容有错。', '',
        '| 考试 / 年份 | 题目记录 | 正式可练 | 有字段修正证据 | 有历史规则提示 |',
        '| --- | ---: | ---: | ---: | ---: |']
    for exam, year in sorted({(r['exam'], str(r['year'])) for r in rows}):
        group = [r for r in rows if r['exam'] == exam and str(r['year']) == year]
        report.append(f"| {exam} / {year} | {len(group)} | "
            f"{sum(r['review_status'] == 'approved' and r['usage'] == 'practice' for r in group)} | "
            f"{sum(bool(r['historical_fixed_fields']) for r in group)} | {sum(bool(r['prior_rule_flags']) for r in group)} |")
    report += ['', '## 阅读与登记', '',
        f"文章 {len(passages)} 篇，其中 {summary['passages_with_body_patch_evidence']} 篇有正文修正证据。",
        f"独立审核登记 {len(records)} 条。题目登记状态：{summary['question_record_statuses']}。",
        '文章正文和题干、选项、答案分别登记；不以修正一个字段代表全题通过。词库不在本导出范围。', '',
        '## 优先核对清单', '', '以下来自旧规则报告，本次未重新扫描；命中提示不等于确定错误。', '']
    for row in rows:
        if row['prior_rule_flags']:
            report.append(f"- {row['exam']} {row['year']} 原题 {row['number']}（ID {row['question_id']}，"
                f"页 {row['source_page']}）：{row['prior_rule_flags']}；{row['record_status']}")
    (out / 'README.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default=str(ROOT / 'database/russian_ai_tutor.sqlite'))
    parser.add_argument('--out', default=str(ROOT / 'data/processed/review_coverage'))
    parser.add_argument('--records', default=str(ROOT / 'data/review_records/content_reviews.jsonl'))
    args = parser.parse_args()
    print(json.dumps(export(args.db, args.out, args.records), ensure_ascii=False, indent=2))
