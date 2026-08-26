from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED = {
    2017: {'listening_choice': 15, 'grammar_choice': 40, 'culture_choice': 5, 'reading_choice': 20},
    2018: {'listening_choice': 15, 'grammar_choice': 40, 'culture_choice': 5, 'reading_choice': 20},
    2019: {'listening_choice': 15, 'grammar_choice': 40, 'culture_choice': 5, 'reading_choice': 20},
    2021: {'listening_choice': 15, 'grammar_choice': 40, 'culture_choice': 5, 'reading_choice': 20},
    2022: {'listening_choice': 15, 'grammar_choice': 40, 'culture_choice': 5, 'reading_choice': 20},
    2023: {'listening_choice': 15, 'grammar_choice': 40, 'culture_choice': 5, 'reading_choice': 20},
    2024: {'listening_choice': 15, 'grammar_choice': 50, 'culture_choice': 5, 'reading_choice': 20},
}


def validate(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding='utf-8'))
    year = int(payload.get('source_year'))
    questions = payload.get('questions', [])
    counts: dict[str, int] = {}
    missing_options: list[str] = []
    missing_answers: list[str] = []
    missing_passages: list[str] = []
    wrong_numbers: list[str] = []
    for question in questions:
        number = str(question.get('source_question_number') or '')
        qtype = str(question.get('question_type') or '')
        counts[qtype] = counts.get(qtype, 0) + 1
        if len(question.get('options') or []) != 4:
            missing_options.append(number)
        if not question.get('correct_answer'):
            missing_answers.append(number)
        if qtype == 'reading_choice' and not (question.get('passage') or {}).get('body'):
            missing_passages.append(number)
        if question.get('exam_system') != 'TEM4_RU' or question.get('level') != 'TEM4':
            wrong_numbers.append(number)
    expected = EXPECTED[year]
    errors: list[str] = []
    if counts != expected:
        errors.append(f'counts expected {expected}, got {counts}')
    if missing_options:
        errors.append('invalid option count: ' + ','.join(missing_options))
    if missing_answers:
        errors.append('missing answers: ' + ','.join(missing_answers))
    if missing_passages:
        errors.append('missing reading passages: ' + ','.join(missing_passages))
    if wrong_numbers:
        errors.append('wrong exam metadata: ' + ','.join(wrong_numbers))
    if payload.get('exam_system') != 'TEM4_RU' or payload.get('level') != 'TEM4':
        errors.append('payload must be TEM4_RU/TEM4')
    return {'file': str(path), 'source_year': year, 'counts': counts, 'question_total': len(questions), 'missing_options': missing_options, 'missing_answers': missing_answers, 'errors': errors}


def main() -> None:
    parser = argparse.ArgumentParser(description='Validate TEM4 segmented review JSON files.')
    parser.add_argument('paths', nargs='+', type=Path)
    args = parser.parse_args()
    results = [validate(path) for path in args.paths]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if any(item['errors'] for item in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
