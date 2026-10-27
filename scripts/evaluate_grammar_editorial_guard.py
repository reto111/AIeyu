"""Local replay only: scope contrast cases, preserved retrieval sets and pilot."""
import json
from pathlib import Path
from grammar_editorial_guard import prepare, validate_response
from grammar_editorial_rag import DEFAULT_DB, sha
from run_grammar_generation_pilot import ROOT, OUT, write, now

BASE = ROOT / 'data/processed/grammar_reference/rag'
REPORT = BASE / 'guard_acceptance_20261022_001.json'

def main():
    if REPORT.exists():
        raise FileExistsError('Preserve reports; choose another output')
    frozen_path = BASE / 'guard_scope_cases_20261022_001.json'
    frozen = json.loads(frozen_path.read_text(encoding='utf-8'))
    assert sha(DEFAULT_DB) == frozen['source_sha256']
    binding = {'frozen_at': now(), 'source_sha256': sha(DEFAULT_DB),
               'scope_cases_sha256': sha(frozen_path),
               'code_sha256': {name: sha(ROOT/'scripts'/name) for name in
                   ['grammar_editorial_guard.py', 'grammar_editorial_rag.py',
                    'grammar_editorial_search_candidate.py', 'grammar_question_search.py',
                    'evaluate_grammar_editorial_guard.py']}}
    write(BASE / 'guard_run_binding_20261022_001.json', binding)
    scope_records = []
    for case in frozen['cases']:
        packet = prepare(case['question'])
        scope_records.append({**case, 'actual_scope': packet['scope']['decision'],
            'expected_met': packet['scope']['decision'] == case['expected_scope'],
            'status': packet['status'], 'prompt_present': packet['prompt_package'] is not None,
            'reasons': packet['scope']['reasons']})
    old_overlap = json.loads((BASE/'editorial_overlap_cases_20261022_001.json').read_text(encoding='utf-8'))
    overlap = []
    for question in old_overlap['questions']:
        packet = prepare(question)
        overlap.append({'question': question, 'scope': packet['scope'],
                        'prompt_present': packet['prompt_package'] is not None})
    retrieval = []
    for filename, split in [('editorial_retrieval_cases_20261022_001.json','development40'),
                            ('editorial_candidate_newcases_20261022_001.json','new20')]:
        data = json.loads((BASE/filename).read_text(encoding='utf-8'))
        for case in data['cases']:
            packets = {name: prepare(case['question'], retriever=name)
                       for name in ['baseline','candidate_v1']}
            row = {'id': case.get('id',case.get('case_id')), 'split': split,
                   'question': case['question'], 'expected_codes': case['expected_codes']}
            for name, packet in packets.items():
                sources = (packet['evidence_packet'] or {}).get('sources', [])
                codes = [s['code'] for s in sources]
                row[name] = {'codes': codes, 'scope': packet['scope']['decision'],
                    'all_expected': all(c in codes for c in case['expected_codes']) if case['expected_codes'] else None}
            retrieval.append(row)
    replay = []
    for path in sorted((OUT/'responses').glob('*_rag.json')):
        response = json.loads(path.read_text(encoding='utf-8'))
        request = json.loads((OUT/'requests'/path.name).read_text(encoding='utf-8'))
        question = json.loads(request['messages'][1]['content'])['question']
        packet = prepare(question)
        row = {'request_id': path.stem, 'status': packet['status'],
               'prompt_present': packet['prompt_package'] is not None,
               'limits': '旧响应的本地校验重放，未在新提示词下生成。'}
        if packet['status'] == 'prepared':
            try:
                result = validate_response(packet, response['parsed'], question=question)
                row['validation'] = result
            except ValueError as exc:
                row['validation'] = {'valid': False, 'error': str(exc)}
        replay.append(row)
    summary = {'scope_expected': sum(r['expected_met'] for r in scope_records),
               'scope_total': len(scope_records),
               'overlap_requests_without_prompt': sum(not r['prompt_present'] for r in overlap),
               'overlap_total': len(overlap),
               'pilot_answered_valid': sum(r.get('validation',{}).get('valid',False) for r in replay),
               'pilot_requests_withheld': sum(not r['prompt_present'] for r in replay)}
    for split in ['development40','new20']:
        rows = [r for r in retrieval if r['split'] == split and r['expected_codes']]
        summary[split] = {'positive_total': len(rows),
            **{name: sum(r[name]['all_expected'] for r in rows) for name in ['baseline','candidate_v1']},
            'unexpected_scope_blocks': [r['id'] for r in rows if r['baseline']['scope'] != 'allow']}
    assert sha(DEFAULT_DB) == frozen['source_sha256']
    write(REPORT, {'evaluated_at': now(), 'run_binding': binding, 'summary': summary,
        'scope_records': scope_records, 'old_overlap_replay': overlap,
        'retrieval_records': retrieval, 'pilot_response_replay': replay,
        'api_calls': 0, 'default_entry_changed': False,
        'limitations': ['有限关键词范围规则，不是语义充分性判定或通用范围外分类器。',
                        '新题由同一助手设计，不是独立专家盲评。',
                        '旧生成响应未重试或修复，旧实验结果保留。']})
    print(json.dumps({'artifact': str(REPORT), 'summary': summary,
                      'scope_misses': [r for r in scope_records if not r['expected_met']]}, ensure_ascii=False))

if __name__ == '__main__':
    main()
