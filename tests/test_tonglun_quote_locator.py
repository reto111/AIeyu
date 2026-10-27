"""Provenance failures and ambiguous/cross-page quotes on synthetic sources."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from tonglun_quote_locator import locate_in_trace, trace_ready_section


class TonglunQuoteLocatorTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.db.executescript('CREATE TABLE chunks(code,title,body,pdf_pages,printed_pages,status,notes); CREATE TABLE pages(pdf_page,review_json,review_sha256);')
        self.source = dict(title='synthetic', path='synthetic.pdf', sha256='synthetic')
        self.parts = ['重复短句。по**ёт**。跨页', '连接。重复短句。']
        for i, body in enumerate(self.parts, 10):
            page = dict(printed_page=str(i-9), review_method='visual_comparison', fragments=[dict(code='unit', title='title', body=body, start=i==10, end=i==11)])
            text = json.dumps(page, ensure_ascii=False)
            self.db.execute('INSERT INTO pages VALUES(?,?,?)', (i, text, hashlib.sha256(text.encode('utf8')).hexdigest()))
        self.db.execute('INSERT INTO chunks VALUES(?,?,?,?,?,?,?)', ('unit','title',''.join(self.parts),'[10,11]','["1","2"]','ready','[]'))

    def tearDown(self):
        self.db.close()

    def test_repeated_quote_preserves_both_pages(self):
        result = locate_in_trace(trace_ready_section(self.db,'unit',self.source),'重复短句')
        self.assertTrue(result['ambiguous'])
        self.assertEqual([x['pdf_pages'] for x in result['occurrences']], [[10],[11]])

    def test_cross_page_quote_has_both_anchors(self):
        result = locate_in_trace(trace_ready_section(self.db,'unit',self.source),'跨页连接')
        self.assertEqual(result['occurrences'][0]['pdf_pages'],[10,11])
        self.assertEqual(len(result['occurrences'][0]['page_fragment_spans']),2)

    def test_formatting_removed_but_yo_and_stress_not_invented(self):
        trace = trace_ready_section(self.db,'unit',self.source)
        self.assertTrue(locate_in_trace(trace,'поёт')['quote_found'])
        for quote in ('поет','поё́т','по**ёт**'):
            self.assertFalse(locate_in_trace(trace,quote)['quote_found'])

    def test_isolated_and_stale_body_rejected(self):
        self.db.execute("UPDATE chunks SET status='unresolved'")
        with self.assertRaises(ValueError):trace_ready_section(self.db,'unit',self.source)
        self.db.execute("UPDATE chunks SET status='ready',body='forged'")
        with self.assertRaises(ValueError):trace_ready_section(self.db,'unit',self.source)

    def test_page_tampering_rejected(self):
        self.db.execute("UPDATE pages SET review_json='{}' WHERE pdf_page=10")
        with self.assertRaises(ValueError):trace_ready_section(self.db,'unit',self.source)

    def test_unclosed_boundary_rejected_even_with_valid_hash(self):
        page=json.loads(self.db.execute('SELECT review_json FROM pages WHERE pdf_page=11').fetchone()[0])
        page['fragments'][0]['end']=False
        text=json.dumps(page,ensure_ascii=False)
        self.db.execute('UPDATE pages SET review_json=?,review_sha256=? WHERE pdf_page=11',(text,hashlib.sha256(text.encode('utf8')).hexdigest()))
        with self.assertRaises(ValueError):trace_ready_section(self.db,'unit',self.source)

    def test_empty_quote_rejected(self):
        trace=trace_ready_section(self.db,'unit',self.source)
        for quote in ('', ' ', None, 'a'*1025):
            with self.assertRaises(ValueError):locate_in_trace(trace,quote)


if __name__ == '__main__':
    unittest.main()
