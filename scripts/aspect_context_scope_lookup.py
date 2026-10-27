"""Return frozen paragraph context notes without assigning example labels."""
import argparse
import hashlib
import json
from pathlib import Path

REPORT = 'data/processed/aspect_reference/reviews/negative_scope_screen_20261026_001.json'
REPORT_SHA256 = '755b8af4ece9ee92b8a52e7252ab19850fb1e44820722ebc2cf027df8c88c08e'
VISUAL = 'data/processed/aspect_reference/reviews/negative_scope_visual_review_20261026_001.json'
VISUAL_SHA256 = '253490542c42e7c8d6b5e71213414f986c0615534da3eaed9e029719f256bc8c'
CASE = 'data/processed/aspect_reference/reviews/rejected_reading_context_case_20261026_001.json'
CASE_SHA256 = '716a3532782631c400e7bd45c8b94f3ccc27ec7850f738d7d7f3144199930c2b'


def pinned_file(workspace, relative, expected):
    target = (workspace / relative).resolve()
    if not target.is_relative_to(workspace):
        raise ValueError('Source path escapes workspace')
    data = target.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('Frozen source fingerprint mismatch: ' + relative)
    return data


def lookup(workspace, *, example_id=None, residual_id=None, include_candidates=False):
    if bool(example_id) == bool(residual_id):
        raise ValueError('Choose exactly one example_id or residual_id')
    workspace = Path(workspace).resolve()
    report = json.loads(pinned_file(workspace, REPORT, REPORT_SHA256))
    visual = json.loads(pinned_file(workspace, VISUAL, VISUAL_SHA256))
    case = json.loads(pinned_file(workspace, CASE, CASE_SHA256))
    if visual['screen_report_sha256'] != REPORT_SHA256:
        raise ValueError('Visual review refers to another screen')
    for relative, expected in report['source_file_pins'].items():
        pinned_file(workspace, relative, expected)
    visual_records = {r['residual_id']: r for r in visual['records']}
    matches = []
    for record in report['records']:
        source = record['source_paragraph']
        if source['state'] == 'withheld':
            continue
        if source['state'] != 'original_source_ready' and not include_candidates:
            continue
        overlap_ids = {r['example_id'] for r in record['overlapping_existing_examples']}
        reference_ids = set()
        if source['residual_id'] == case['source_paragraph']['residual_id']:
            if source != case['source_paragraph']:
                raise ValueError('Explicit reference case/source mismatch')
            reference_ids = {r['example_id'] for r in case['referenced_examples']}
        if residual_id != source['residual_id'] and (example_id is None or example_id not in overlap_ids | reference_ids):
            continue
        page_review = visual_records[source['residual_id']]
        if page_review['source_text_sha256'] != source['source_text_sha256']:
            raise ValueError('Visual/source paragraph mismatch')
        matches.append(dict(
            residual_id=source['residual_id'], source_unit=source['source_unit'],
            source_state=source['state'], source_start=source['source_start'],
            source_end=source['source_end'], source_text=source['source_text'],
            source_text_sha256=source['source_text_sha256'],
            candidate_text=source['candidate_text'],
            candidate_text_sha256=source['candidate_text_sha256'],
            page_evidence=source['page_evidence'], edits=source['edits'],
            assistant_paragraph_context_category=record['assistant_primary_context_category'],
            reason_zh=record['reason_zh'],
            relation=('explicit_author_example_reference' if example_id in reference_ids
                      else 'geometric_overlap_only' if example_id else 'requested_source_paragraph'),
            category_is_example_label=False, independent_review=False,
            visual_review_pdf_pages=[p['pdf_page'] for p in source['page_evidence']],
        ))
    return dict(
        example_id=example_id, residual_id=residual_id,
        include_candidates=include_candidates, matches=matches,
        review_scope_exhaustive=False, examples_added=0, labels_assigned=0,
        source_report=REPORT, source_report_sha256=REPORT_SHA256,
        visual_review=VISUAL, visual_review_sha256=VISUAL_SHA256,
        explicit_reference_case=CASE, explicit_reference_case_sha256=CASE_SHA256,
        verified_inputs='three_frozen_review_reports_and_three_source_jsonl_files',
        interpretation_zh='段落阅读备注；与指定例证的交叠不等于否定作用域归属。空返回仅表示本筛查无可用备注，不表示该例句可接受或无上下文限制。原页图像的核查记录已绑定，此入口不重新读取图像。',
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path(__file__).resolve().parents[1])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--example-id')
    group.add_argument('--residual-id')
    parser.add_argument('--include-candidates', action='store_true')
    args = parser.parse_args()
    try:
        result = lookup(args.workspace, example_id=args.example_id, residual_id=args.residual_id,
                        include_candidates=args.include_candidates)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, str(exc) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
