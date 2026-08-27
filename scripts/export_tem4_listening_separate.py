from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description='Export TEM4 listening items for separate storage; never writes to SQLite.')
    parser.add_argument('inputs', nargs='+', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for path in args.inputs:
        payload = json.loads(path.read_text(encoding='utf-8'))
        listening = [item for item in payload.get('questions', []) if item.get('question_type') == 'listening_choice']
        output = args.output_dir / path.name
        export = {
            'source_file': payload.get('source_file'),
            'source_year': payload.get('source_year'),
            'exam_system': payload.get('exam_system'),
            'level': payload.get('level'),
            'question_type': 'listening_choice',
            'storage_policy': 'separate_reference_only_not_imported_to_question_database',
            'questions': listening,
        }
        output.write_text(json.dumps(export, ensure_ascii=False, indent=2), encoding='utf-8')
        results.append({'source_year': payload.get('source_year'), 'count': len(listening), 'output': str(output).replace('\\', '/')})
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
