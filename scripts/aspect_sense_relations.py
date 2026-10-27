"""Read source-bound, sense-specific textbook relations without labeling corpus data."""
import argparse
import hashlib
import json
import re
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / 'data/processed/aspect_reference/research_exports/aspect_sense_relations_20261026_001'
KINDS = ['sense_specific_aspect_counterpart', 'book_lexical_class_membership', 'qualified_unpaired_usage_in_sense']


def digest(value):
    return hashlib.sha256(value.encode('utf8')).hexdigest()


def load(collection):
    collection = Path(collection).resolve()
    manifest = json.loads((collection / 'manifest.json').read_text('utf8'))
    for name, expected in manifest['files'].items():
        path = (collection / name).resolve()
        if not path.is_relative_to(collection):
            raise ValueError('Relation file outside collection')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Changed relation payload')
    unit = json.loads((collection / 'source_unit.json').read_text('utf8'))
    if (digest(unit['source_text']) != unit['source_unit_sha256']
            or digest(unit['candidate_text']) != unit['candidate_unit_sha256']
            or unit['source_text'] != unit['candidate_text'] or unit['edits']):
        raise ValueError('Unexpected frozen source/candidate snapshot')
    contexts = {r['residual_id']: r for r in json.loads((collection / 'context.json').read_text('utf8'))}
    for context in contexts.values():
        if (context['source_unit_sha256'] != unit['source_unit_sha256']
                or context['candidate_unit_sha256'] != unit['candidate_unit_sha256']):
            raise ValueError('Context unit binding mismatch')
        if unit['source_text'][context['source_start']:context['source_end']] != context['source_text']:
            raise ValueError('Context range mismatch')
        if digest(context['source_text']) != context['source_text_sha256']:
            raise ValueError('Context hash mismatch')
    rows = [json.loads(line) for line in (collection / 'relations.jsonl').read_text('utf8').splitlines()]
    seen = set()
    for row in rows:
        if row['relation_id'] in seen:
            raise ValueError('Duplicate relation ID')
        seen.add(row['relation_id'])
        context = contexts[row['source_residual_id']]
        if (row['source_unit_sha256'] != unit['source_unit_sha256']
                or row['candidate_unit_sha256'] != unit['candidate_unit_sha256']
                or row['source_context_sha256'] != context['source_text_sha256']
                or row['source_state'] != context['state']):
            raise ValueError('Relation/context binding mismatch')
        for role, part in row['source_fragments'].items():
            a, b = part['source_start'], part['source_end']
            if not context['source_start'] <= a < b <= context['source_end']:
                raise ValueError('Fragment outside source paragraph')
            if unit['source_text'][a:b] != part['source_text'] or digest(part['source_text']) != part['source_text_sha256']:
                raise ValueError('Fragment source mismatch')
            if role in ['lemma', 'imperfective', 'perfective']:
                raw = unit['source_text']
                if (not re.fullmatch('[А-Яа-яЁё]+', part['source_text'])
                        or a > 0 and re.fullmatch('[А-Яа-яЁё]', raw[a - 1])
                        or b < len(raw) and re.fullmatch('[А-Яа-яЁё]', raw[b])):
                    raise ValueError('Lemma fragment is not a complete Cyrillic word')
        fragments = row['source_fragments']
        if row['relation_type'] == KINDS[0]:
            fields = [('imperfective_lemma', 'imperfective'), ('sense_zh', 'sense'), ('perfective_lemma', 'perfective')]
        elif row['relation_type'] == KINDS[1]:
            fields = [('lemma', 'lemma'), ('class_label_zh', 'class_label')]
        elif row['relation_type'] == KINDS[2]:
            fields = [('lemma', 'lemma'), ('sense_zh', 'sense')]
            qualifier = fragments['qualification']['source_text']
            if (not all(word in qualifier for word in ['有些', '常常'])
                    or row['assertion_strength'] != '有些/常常'
                    or row['counterpart_lemma'] is not None
                    or row['counterpart_status'] != 'former_perfective_not_named_in_this_passage'):
                raise ValueError('Qualified assertion strengthened or invented')
        else:
            raise ValueError('Unknown relation type')
        if any(row[field] != fragments[fragment]['source_text'] for field, fragment in fields):
            raise ValueError('Relation field differs from source fragment')
    return rows, contexts


def select(rows, lemma=None, kind=None, include_candidates=False):
    allowed = {'original_source_ready', 'model_editorial_candidate'} if include_candidates else {'original_source_ready'}
    if lemma is not None and not lemma.strip():
        raise ValueError('Nonempty lemma required')
    return [r for r in rows if r['source_state'] in allowed
            and (kind is None or r['relation_type'] == kind)
            and (lemma is None or lemma.casefold() in {
                r.get(field, '').casefold() for field in ['lemma', 'imperfective_lemma', 'perfective_lemma']})]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', type=Path, default=DEFAULT)
    parser.add_argument('--lemma')
    parser.add_argument('--kind', choices=KINDS)
    parser.add_argument('--include-candidates', action='store_true')
    args = parser.parse_args()
    try:
        rows, contexts = load(args.collection)
        chosen = select(rows, args.lemma, args.kind, args.include_candidates)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, str(exc) + '\n')
    print(json.dumps(dict(records=chosen, source_contexts={
        r['source_residual_id']: contexts[r['source_residual_id']] for r in chosen},
        matching_relations=len(chosen), exact_lemma_match=True, natural_corpus_labels_assigned=0,
        independent_review=False, warning_zh='教材义项与类别关系，只描述所引段落；无结果不表示不存在体词偶。'),
        ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
