"""Query historical claim reading separately from targeted contextual evidence."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / 'data/processed/aspect_reference/research_exports/aspect_claim_context_support_20261027_001'


def digest(value):
    return hashlib.sha256(value.encode('utf8')).hexdigest()


def read(path):
    return json.loads(path.read_text('utf8'))


def claim_key(row):
    return row['code'], row.get('claim_number', row.get('claim_index', row.get('claim')))


def boundary(position, edits):
    delta = 0
    for edit in sorted(edits, key=lambda r: r['start']):
        start, old, new = edit['start'], edit['old'], edit['new']
        end = start + len(old)
        if end <= position:
            delta += len(new) - len(old)
        elif start < position < end:
            prefix = 0
            while prefix < min(len(old), len(new)) and old[prefix] == new[prefix]:
                prefix += 1
            suffix = 0
            while suffix < min(len(old), len(new)) - prefix and old[-suffix - 1] == new[-suffix - 1]:
                suffix += 1
            if position <= start + prefix:
                return position + delta
            if position >= end - suffix:
                return start + delta + len(new) - (end - position)
            raise ValueError('Context boundary cuts changed text')
        elif start >= position:
            break
    return position + delta


def load(root):
    root = Path(root).resolve()
    manifest = read(root / 'manifest.json')
    for name, expected in manifest['files'].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Changed or outside claim context payload: ' + name)
    claims = [json.loads(s) for s in (root / 'claims.jsonl').read_text('utf8').splitlines()]
    indexed = {claim_key(r): r for r in claims}
    if len(indexed) != len(claims):
        raise ValueError('Duplicate claim key')
    coverage = read(root / 'coverage.json')
    ledger = {claim_key(r): r for r in coverage['records']}
    pairs = {claim_key(r): r for r in read(root / 'paired_reading.json')['records']}
    screened = {claim_key(r): r for r in read(root / 'keyword_screen.json')['records']}
    if set(indexed) != set(ledger) or set(indexed) != set(pairs):
        raise ValueError('Reading coverage keys differ from claims')
    units = read(root / 'source_units.json')
    pins = read(root / 'source_unit_pins.json')
    for code, unit in units.items():
        expected = pins[code]
        if (digest(unit['source_text']) != expected['source_unit_sha256']
                or digest(unit['candidate_text']) != expected['candidate_unit_sha256']
                or unit['source_unit_sha256'] != expected['source_unit_sha256']
                or unit['candidate_unit_sha256'] != expected['candidate_unit_sha256']
                or unit['state'] != expected['state']):
            raise ValueError('Source unit binding changed')
        raw = unit['source_text']
        parts, cursor = [], 0
        for edit in sorted(unit['edits'], key=lambda r: r['start']):
            start, old, new = edit['start'], edit['old'], edit['new']
            if start < cursor or raw[start:start + len(old)] != old:
                raise ValueError('Stale unit edit')
            parts.extend([raw[cursor:start], new])
            cursor = start + len(old)
        if ''.join(parts) + raw[cursor:] != unit['candidate_text']:
            raise ValueError('Candidate replay changed')

    def span(code, part):
        unit = units[code]
        for field in ['source_unit_sha256', 'candidate_unit_sha256']:
            if field in part and part[field] != pins[code][field]:
                raise ValueError('Context/unit binding differs from frozen review')
        a, b = part['source_start'], part['source_end']
        text = part.get('text', part.get('source_text'))
        if not isinstance(a, int) or not isinstance(b, int) or not 0 <= a < b <= len(unit['source_text']):
            raise ValueError('Invalid source span')
        if (unit['source_text'][a:b] != text
                or digest(text) != part.get('sha256', part.get('source_text_sha256'))):
            raise ValueError('Changed source span')
        if 'candidate_text' in part:
            left, right = boundary(a, unit['edits']), boundary(b, unit['edits'])
            if (unit['candidate_text'][left:right] != part['candidate_text']
                    or digest(part['candidate_text']) != part['candidate_text_sha256']):
                raise ValueError('Changed candidate span')

    reports = {}
    context_ranges = 0
    for name, spec in manifest['reviews'].items():
        path = root / spec['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != spec['sha256']:
            raise ValueError('Frozen review changed')
        report = read(path)
        if (report.get('cards_manifest_sha256', report.get('collection_manifest_sha256')) != manifest['source_cards_manifest_sha256']
                or report['candidate_manifest_sha256'] != manifest['source_candidate_manifest_sha256']):
            raise ValueError('Review belongs to another source edition')
        reports[name] = report
        for row in report['records']:
            key = claim_key(row)
            claim = indexed[key]
            if (row.get('model_claim', row.get('claim_text')) != claim['text_zh']
                    or row.get('original_quote', row.get('existing_quote')) != claim['quote']
                    or row.get('source_state', row.get('state')) != claim['state']):
                raise ValueError('Claim differs from frozen review')
            if 'existing_quote_source_start' in row and (row['existing_quote_source_start'] != claim['source_start'] or row['existing_quote_source_end'] != claim['source_end']):
                raise ValueError('Reviewed quote offsets differ from claim')
            for field in ['source_unit_sha256', 'candidate_unit_sha256']:
                if row[field] != pins[key[0]][field]:
                    raise ValueError('Reviewed claim/unit binding changed')
            for part in row.get('supplementary_evidence', row.get('supplemental_context')):
                span(part.get('source_code', key[0]), part)
                context_ranges += 1
        for observation in report.get('additional_observations', []):
            for part in observation['source_fragments']:
                span(part['source_code'], part)

    for key, claim in indexed.items():
        code = key[0]
        row, pair = ledger[key], pairs[key]
        claim_hash, quote_hash = digest(claim['text_zh']), digest(claim['quote'])
        if (claim_hash != row['claim_text_sha256'] or claim_hash != pair['claim_text_sha256']
                or quote_hash != claim['quote_sha256'] or quote_hash != row['quote_sha256']
                or quote_hash != pair['quote_sha256'] or claim['state'] != units[code]['state']
                or units[code]['source_text'][claim['source_start']:claim['source_end']] != claim['quote']
                or not row['paired_reading_recorded'] or not pair['read_as_pair_this_pass']):
            raise ValueError('Historical claim/quote reading binding changed')
        if row['targeted_context_review_recorded'] != bool(row['targeted_context_events']):
            raise ValueError('Targeted coverage flag differs from events')
        if row['scope_keyword_screen_recorded'] != (key in screened):
            raise ValueError('Keyword screening dimension differs from history')
        if key in screened and (screened[key]['text_zh'] != claim['text_zh'] or screened[key]['quote_sha256'] != quote_hash):
            raise ValueError('Screened claim changed')
        seen = set()
        for event in row['targeted_context_events']:
            identity = event['review'], event['record_index']
            if identity in seen:
                raise ValueError('Repeated review event')
            seen.add(identity)
            spec = manifest['reviews'][event['review']]
            if event['review_sha256'] != spec['sha256']:
                raise ValueError('Event/review fingerprint mismatch')
            reviewed = reports[event['review']]['records'][event['record_index']]
            if (claim_key(reviewed) != key or event['reason_zh'] != reviewed['reason_zh']
                    or event['assessment'] != reviewed.get('single_quote_model_assessment', reviewed.get('assistant_context_judgment'))
                    or event['supplemental_ranges'] != len(reviewed.get('supplementary_evidence', reviewed.get('supplemental_context')))):
                raise ValueError('Event points to another claim or assessment')
        if row['independent_review'] or row['full_claim_entailment_certified']:
            raise ValueError('Independent certification was not recorded')
    actual_events = {(key, event['review'], event['record_index']) for key, row in ledger.items() for event in row['targeted_context_events']}
    expected_events = {(claim_key(row), name, pos) for name, report in reports.items() for pos, row in enumerate(report['records'])}
    if actual_events != expected_events:
        raise ValueError('Review events lost or invented')
    stats = coverage['statistics']
    actual = dict(total_claims=len(claims), historical_paired_reading=len(pairs),
                  historical_keyword_screen=len(screened),
                  targeted_context_review_events=len(actual_events),
                  distinct_targeted_claims=sum(bool(r['targeted_context_events']) for r in ledger.values()),
                  without_targeted_context_record=sum(not r['targeted_context_events'] for r in ledger.values()),
                  supplemental_range_replays=context_ranges)
    if any(stats[k] != v for k, v in actual.items()):
        raise ValueError('Coverage totals differ from records')
    return claims, ledger, reports, actual


def select(claims, ledger, include_candidates=False, code=None, number=None, query=None, only_targeted=False):
    allowed = {'original_source_ready', 'model_editorial_candidate'} if include_candidates else {'original_source_ready'}
    selected = []
    for row in claims:
        if row['state'] not in allowed or code is not None and row['code'] != code or number is not None and row['claim_number'] != number:
            continue
        status = ledger[claim_key(row)]
        if only_targeted and not status['targeted_context_review_recorded']:
            continue
        haystack = row['text_zh'] + ' ' + row['quote']
        if query and not all(term.casefold() in haystack.casefold() for term in query.split()):
            continue
        selected.append(row)
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', type=Path, default=DEFAULT)
    parser.add_argument('command', choices=['stats', 'lookup', 'show'])
    parser.add_argument('--code')
    parser.add_argument('--claim', type=int)
    parser.add_argument('--query')
    parser.add_argument('--only-targeted', action='store_true')
    parser.add_argument('--include-candidates', action='store_true')
    args = parser.parse_args()
    if args.command == 'show' and (args.code is None or args.claim is None):
        parser.error('show requires --code and --claim')
    claims, ledger, reports, totals = load(args.collection)
    selected = select(claims, ledger, args.include_candidates, args.code, args.claim, args.query, args.only_targeted)
    if args.command == 'stats':
        result = dict(total_frozen_coverage=totals, visible_claims=len(selected), visible_targeted_claims=sum(ledger[claim_key(r)]['targeted_context_review_recorded'] for r in selected), source_states=dict(collections.Counter(r['state'] for r in selected)), independent_reviews=0, full_claim_entailment_certified=False)
    else:
        result = []
        for row in selected:
            status = ledger[claim_key(row)]
            context = []
            for event in status['targeted_context_events']:
                reviewed = reports[event['review']]['records'][event['record_index']]
                context.append(dict(review=event['review'], record=reviewed))
            observations = [o for report in reports.values() for o in report.get('additional_observations', []) if o['source_code'] == row['code']]
            result.append(dict(claim=row, reading_status=status, targeted_context=context, unit_observations=observations,
                               interpretation_zh='配对阅读、针对性语境与独立认证分开；无语境记录不等于未读或错误。上下文是教材材料，非自然语料金标。'))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
