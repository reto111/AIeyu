import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from export_content_review_coverage import load_records, review_state


class ReviewCoverageTests(unittest.TestCase):
    def test_no_record_does_not_claim_review(self):
        self.assertEqual(review_state(['question', 1], 'hash', []), ('未登记', None))

    def test_latest_record_and_content_change(self):
        old = {'key': ['question', 1], 'content_hash': 'old', 'verdict': '已核对'}
        latest = {'key': ['question', 1], 'content_hash': 'new', 'verdict': '待确认'}
        self.assertEqual(review_state(['question', 1], 'new', [old, latest])[0], '待确认')
        self.assertEqual(review_state(['question', 1], 'changed', [old, latest])[0], '内容已变化，需复核')

    def test_requires_evidence_and_keeps_original_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'reviews.jsonl'
            self.assertEqual(load_records(path), [])
            record = {'key': ['question', 1], 'content_hash': 'abc', 'fields': ['stem'],
                      'verdict': '已核对', 'reviewer': 'test', 'method': 'source comparison',
                      'source': 'page 3', 'reviewed_at': '2026-09-06'}
            original = json.dumps(record)
            path.write_text(original, encoding='utf-8')
            self.assertEqual(load_records(path), [record])
            self.assertEqual(path.read_text(encoding='utf-8'), original)
            del record['source']
            path.write_text(json.dumps(record), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_records(path)


if __name__ == '__main__':
    unittest.main()
