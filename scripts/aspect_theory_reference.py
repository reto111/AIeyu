"""Query source-bound theory relations and argument cases with explicit source states."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from collections import Counter
sys.dont_write_bytecode = True
from aspect_sense_relations import load as load_senses
from aspect_context_support_verify import replay, candidate_boundary, text_sha

HERE = Path(__file__).resolve().parent
DEFAULT = HERE / 'theory_catalog.json'
if not DEFAULT.exists():
    DEFAULT = HERE.parent / 'data/processed/aspect_reference/theory_catalog_20261026_001.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Theory catalog path outside root')
    return path


def read(path):
    return json.loads(path.read_text('utf8'))


def load(catalog):
    catalog = Path(catalog).resolve()
    base = catalog.parent
    rows, contexts, seen = [], {}, set()
    data = read(catalog)
    kinds = set()
    for item in data['collections']:
        kind = item['key']
        if kind in kinds or kind not in ['sense_relations', 'dictionary_inference_cases']:
            raise ValueError('Duplicate or unknown theory collection')
        kinds.add(kind)
        mp, rp = local(base, item['manifest']), local(base, item['review'])
        if sha(mp) != item['manifest_sha256'] or sha(rp) != item['review_sha256']:
            raise ValueError('Theory collection/review fingerprint mismatch')
        manifest, review = read(mp), read(rp)
        for name, expected in manifest['files'].items():
            if sha(local(mp.parent, name)) != expected:
                raise ValueError('Changed theory payload')
        if manifest['review_sha256'] != item['review_sha256']:
            raise ValueError('Manifest/review binding mismatch')
        if kind == 'sense_relations':
            current, context_rows = load_senses(mp.parent)
            if current != review['relations'] or list(context_rows.values()) != review['source_context']:
                raise ValueError('Sense payload differs from frozen review')
        else:
            current = [json.loads(line) for line in (mp.parent / 'cases.jsonl').read_text('utf8').splitlines()]
            context = read(mp.parent / 'context.json')
            unit = read(mp.parent / 'source_unit.json')
            context_rows = {context['residual_id']: context}
            if current != review['cases'] or context != review['source_context']:
                raise ValueError('Dictionary cases differ from frozen review')
            if (text_sha(unit['source_text']) != context['source_unit_sha256']
                    or text_sha(unit['candidate_text']) != context['candidate_unit_sha256']
                    or replay(unit['source_text'], unit['edits']) != unit['candidate_text']):
                raise ValueError('Dictionary unit binding mismatch')

            def span(part):
                a, b = part['source_start'], part['source_end']
                if not context['source_start'] <= a < b <= context['source_end']:
                    raise ValueError('Argument outside source paragraph')
                if unit['source_text'][a:b] != part['source_text'] or text_sha(part['source_text']) != part['source_text_sha256']:
                    raise ValueError('Dictionary source range mismatch')
                left, right = candidate_boundary(a, unit['edits']), candidate_boundary(b, unit['edits'])
                if unit['candidate_text'][left:right] != part['candidate_text']:
                    raise ValueError('Dictionary candidate range mismatch')
                if part.get('candidate_text_sha256') and text_sha(part['candidate_text']) != part['candidate_text_sha256']:
                    raise ValueError('Dictionary candidate range fingerprint mismatch')
            span(context)
            for row in current:
                if (row['source_unit_sha256'] != context['source_unit_sha256']
                        or row['candidate_unit_sha256'] != context['candidate_unit_sha256']
                        or row['source_state'] != context['state']):
                    raise ValueError('Dictionary case/source binding mismatch')
                span(row)
                for part in row['argument_fragments'].values():
                    span(part)
                for lemma in row['lemmas']:
                    if not re.search('(?<![А-Яа-яЁё])' + re.escape(lemma) + '(?![А-Яа-яЁё])', row['source_text']):
                        raise ValueError('Indexed lemma is not a complete word in case')
        for row in current:
            key = row.get('relation_id', row.get('case_id'))
            if key in seen:
                raise ValueError('Duplicate theory record ID')
            seen.add(key)
            rows.append(dict(theory_record_id=key, theory_record_kind=kind, **row))
        contexts.update(context_rows)
    if kinds != {'sense_relations', 'dictionary_inference_cases'}:
        raise ValueError('Missing theory collection')
    return rows, contexts


def choose(rows, include_candidates=False, kind=None, lemma=None, record_id=None):
    states = {'original_source_ready', 'model_editorial_candidate'} if include_candidates else {'original_source_ready'}
    result = []
    for row in rows:
        if row['source_state'] not in states or kind and row['theory_record_kind'] != kind:
            continue
        if record_id and row['theory_record_id'] != record_id:
            continue
        tags = row.get('lemmas', []) + [row.get(k, '') for k in ['lemma', 'imperfective_lemma', 'perfective_lemma']]
        if lemma and lemma.casefold() not in {value.casefold() for value in tags}:
            continue
        result.append(row)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['stats', 'lookup', 'show'])
    parser.add_argument('--catalog', type=Path, default=DEFAULT)
    parser.add_argument('--lemma')
    parser.add_argument('--id')
    parser.add_argument('--kind', choices=['sense_relations', 'dictionary_inference_cases'])
    parser.add_argument('--include-candidates', action='store_true')
    args = parser.parse_args()
    if args.command == 'lookup' and (not args.lemma or not args.lemma.strip()):
        parser.error('lookup requires nonempty --lemma')
    if args.command == 'show' and not args.id:
        parser.error('show requires --id')
    try:
        rows, contexts = load(args.catalog)
        selected = choose(rows, args.include_candidates, args.kind,
                          args.lemma if args.command == 'lookup' else None,
                          args.id if args.command == 'show' else None)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, str(exc) + '\n')
    result = dict(catalog_sha256=sha(args.catalog), matching_records=len(selected),
                  by_kind=dict(Counter(r['theory_record_kind'] for r in selected)),
                  by_source_state=dict(Counter(r['source_state'] for r in selected)),
                  natural_corpus_labels_assigned=0, independent_review=False,
                  warning_zh='教材关系与论证案例；不是新增语料组、辞书全义项或普遍可接受性标签。无结果不表示理论关系不存在。')
    if args.command != 'stats':
        result.update(records=selected, source_contexts={r['source_residual_id']: contexts[r['source_residual_id']] for r in selected})
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
