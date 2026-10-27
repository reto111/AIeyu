"""Replay contextual evidence against frozen source/candidate unit snapshots."""
import argparse
import hashlib
import json
from pathlib import Path


def text_sha(value):
    return hashlib.sha256(value.encode('utf8')).hexdigest()


def read(path):
    return json.loads(path.read_text('utf8'))


def local(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Outside context support')
    return path


def replay(raw, edits):
    parts = []
    cursor = 0
    for edit in sorted(edits, key=lambda e: e['start']):
        a, old, new = edit['start'], edit['old'], edit['new']
        if a < cursor or raw[a:a + len(old)] != old:
            raise ValueError('Stale unit edit')
        parts.extend([raw[cursor:a], new])
        cursor = a + len(old)
    return ''.join(parts) + raw[cursor:]


def candidate_boundary(position, edits):
    delta = 0
    for edit in sorted(edits, key=lambda e: e['start']):
        a, old, new = edit['start'], edit['old'], edit['new']
        b = a + len(old)
        if b <= position:
            delta += len(new) - len(old)
        elif a < position < b:
            prefix = 0
            while prefix < min(len(old), len(new)) and old[prefix] == new[prefix]:
                prefix += 1
            suffix = 0
            while suffix < min(len(old), len(new)) - prefix and old[-suffix - 1] == new[-suffix - 1]:
                suffix += 1
            if position <= a + prefix:
                return position + delta
            if position >= b - suffix:
                return a + delta + len(new) - (b - position)
            raise ValueError('Range boundary cuts changed text')
        elif a >= position:
            break
    return position + delta


def verify(root):
    root = Path(root).resolve()
    manifest = read(root / 'manifest.json')
    for name, expected in manifest['files'].items():
        if hashlib.sha256(local(root, name).read_bytes()).hexdigest() != expected:
            raise ValueError('Changed context file: ' + name)
    reports = {key: read(local(root, item['path'])) for key, item in manifest['reviews'].items()}
    for item in manifest['reviews'].values():
        if hashlib.sha256(local(root, item['path']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Review fingerprint mismatch')
    units = read(root / 'source_units.json')
    for unit in units.values():
        if text_sha(unit['source_text']) != unit['source_unit_sha256']:
            raise ValueError('Source snapshot hash mismatch')
        if text_sha(unit['candidate_text']) != unit['candidate_unit_sha256']:
            raise ValueError('Candidate snapshot hash mismatch')
        if replay(unit['source_text'], unit['edits']) != unit['candidate_text']:
            raise ValueError('Candidate unit replay mismatch')
    counts = dict(source_units=len(units), source_ranges=0, candidate_ranges=0)

    def span(code, part):
        unit = units[code]
        for key in ['source_unit_sha256', 'candidate_unit_sha256']:
            if key in part and unit[key] != part[key]:
                raise ValueError('Unit binding differs from frozen review')
        a, b = part['source_start'], part['source_end']
        value = part.get('source_text', part.get('text'))
        if not isinstance(a, int) or not isinstance(b, int) or not 0 <= a < b <= len(unit['source_text']):
            raise ValueError('Invalid source range')
        if unit['source_text'][a:b] != value:
            raise ValueError('Source range differs from snapshot')
        expected = part.get('source_text_sha256', part.get('text_sha256'))
        if expected and text_sha(value) != expected:
            raise ValueError('Source range fingerprint mismatch')
        counts['source_ranges'] += 1
        if 'candidate_text' in part:
            left = candidate_boundary(a, unit['edits'])
            right = candidate_boundary(b, unit['edits'])
            if unit['candidate_text'][left:right] != part['candidate_text']:
                raise ValueError('Candidate range differs from unit replay')
            if part.get('candidate_text_sha256') and text_sha(part['candidate_text']) != part['candidate_text_sha256']:
                raise ValueError('Candidate range fingerprint mismatch')
            counts['candidate_ranges'] += 1

    scope = reports['scope']
    for record in scope['records']:
        paragraph = record['source_paragraph']
        code = paragraph['source_unit']
        span(code, paragraph)
        for hit in record['literal_cue_occurrences']:
            span(code, {**hit, 'text': hit['cue']})
    visual = reports['visual']
    if visual['screen_report_sha256'] != manifest['reviews']['scope']['sha256']:
        raise ValueError('Visual review/screen mismatch')
    byid = {r['source_paragraph']['residual_id']: r for r in scope['records']}
    for row in visual['records']:
        original = byid[row['residual_id']]
        if row['source_text_sha256'] != original['source_paragraph']['source_text_sha256'] or row['context_category_retained'] != original['assistant_primary_context_category']:
            raise ValueError('Visual context binding mismatch')

    rejected = reports['rejected']
    code = rejected['source_paragraph']['source_unit']
    span(code, rejected['source_paragraph'])
    span(code, rejected['positive_framing'])
    for row in rejected['referenced_examples'] + rejected['rejected_interpretations']:
        span(code, row)

    translations = reports['translations']
    code = translations['source_paragraph']['source_unit']
    span(code, translations['source_paragraph'])
    span(code, translations['existing_example'])
    for row in translations['pairs']:
        for key in ['ru', 'zh', 'author_reference_cue']:
            span(code, row[key])
        if not row['ru']['source_end'] < row['zh']['source_start']:
            raise ValueError('Expected noncontiguous translation')
        if row['author_reference_cue']['source_end'] != row['zh']['source_start']:
            raise ValueError('Translation cue no longer adjoins Chinese span')
    ordered = sorted(translations['pairs'], key=lambda r: r['ru']['source_start'])
    if ([r['zh']['source_start'] for r in ordered] != sorted(r['zh']['source_start'] for r in ordered)
            or [r['author_reference_cue']['text'] for r in ordered] != ['第一句是“', '第二句则是“']):
        raise ValueError('Explicit first/second translation ordering changed')

    variants = reports['variants']
    code = variants['source_example']['source_unit']
    for key in ['source_example', 'author_variant_paragraph', 'standalone_clause_discussion']:
        span(code, variants[key])
    for row in variants['relations']:
        for key in ['ru', 'zh_original', 'zh_author_variant']:
            span(code, row[key])
        if row['zh_original']['source_text'].replace('了', '') != row['zh_author_variant']['source_text'].replace('了', ''):
            raise ValueError('Unexpected Chinese variant difference')
    ordered = sorted(variants['relations'], key=lambda r: r['ru']['source_start'])
    for key in ['zh_original', 'zh_author_variant']:
        if [r[key]['source_start'] for r in ordered] != sorted(r[key]['source_start'] for r in ordered):
            raise ValueError('Narrative clause ordering changed')

    reproach = reports['reproach']
    for paragraph in reproach['source_context']:
        span(paragraph['source_unit'], paragraph)
    for row in reproach['relations']:
        original = row['original_numbered_example']
        span(original['source_unit'], original)
        span(original['source_unit'], row['author_paraphrase'])
    if (len(scope['records']), len(visual['visually_checked_pdf_pages']), len(rejected['rejected_interpretations']), len(translations['pairs']), len(variants['relations']), len(reproach['relations'])) != (16, 22, 2, 2, 5, 3):
        raise ValueError('Unexpected frozen contextual scope')
    return dict(verified=True, **counts, scope_paragraphs=16, visual_review_pages=22,
                rejected_readings=2, discontinuous_translations=2, narrative_clause_relations=5,
                reproach_relations=3, new_source_groups=0, independent_semantic_review=False,
                visual_images_included=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        result = verify(args.root)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, str(exc) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
