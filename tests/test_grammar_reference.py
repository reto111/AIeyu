from __future__ import annotations

import copy
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from grammar_reference import dump, file_sha256, import_batch, search


class GrammarReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.pdf = self.root / 'source.pdf'
        with pymupdf.open() as doc:
            for _ in range(4):
                doc.new_page()
            doc.save(self.pdf)
        self.db = self.root / 'grammar.sqlite'
        self.batch = dict(batch_id='a', source_sha256=file_sha256(self.pdf), pages=[
            dict(pdf_page=1, printed_page='1', review_method='visual_comparison', fragments=[
                dict(code='m.1', title='物质名词', body='молоко́ 和 ве', start=True, end=False)])])

    def tearDown(self):
        self.temp.cleanup()

    def load(self, batch=None, apply=True):
        path = self.root / 'batch.json'
        dump(path, batch or self.batch)
        return import_batch(path, db=self.db, apply=apply, pdf=self.pdf)

    def test_preview_no_disk_write_and_incomplete_not_retrieved(self):
        self.assertFalse(self.load(apply=False)['applied'])
        self.assertFalse(self.db.exists())
        self.load()
        self.assertEqual(search('物质名词', db=self.db), [])

    def test_cross_page_join_search_stress_citation_and_backup(self):
        self.load()
        continuation = copy.deepcopy(self.batch)
        continuation['batch_id'] = 'b'
        continuation['pages'][0].update(pdf_page=2, printed_page='2')
        continuation['pages'][0]['fragments'][0].update(body='щество。', start=False, end=True)
        self.assertTrue(Path(self.load(continuation)['backup']).exists())
        rows = search('молоко', db=self.db)
        self.assertEqual(rows[0]['body'], 'молоко́ 和 вещество。')
        self.assertEqual(rows[0]['pdf_pages'], [1, 2])
        self.assertEqual(search('无匹配的查询', db=self.db), [])
        self.assertEqual(search('молоко 不存在的词', db=self.db), [])

    def test_immutable_batch_and_page_conflict(self):
        self.load()
        self.assertEqual(self.load()['result'], 'already_imported')
        changed = copy.deepcopy(self.batch)
        changed['pages'][0]['fragments'][0]['body'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'immutable'):
            self.load(changed)
        changed['batch_id'] = 'b'
        with self.assertRaisesRegex(ValueError, 'already reviewed'):
            self.load(changed)
        with closing(sqlite3.connect(self.db)) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM pages').fetchone()[0], 1)

    def test_word_internal_emphasis_search_preserves_source_and_yo(self):
        ready = copy.deepcopy(self.batch)
        body = '**кни́ж**ный и **книг**ообме́н; `ёлочный`'
        ready['pages'][0]['fragments'][0].update(body=body, end=True)
        self.load(ready)
        for query in ('книжный', 'книгообмен', 'кни́жный', '**книжный**', 'ёлочный'):
            rows = search(query, db=self.db)
            self.assertEqual(rows[0]['code'], 'm.1')
            self.assertEqual(rows[0]['body'], body)
            self.assertEqual(rows[0]['source_sha256'], file_sha256(self.pdf))
        self.assertEqual(search('елочный', db=self.db), [])
        self.assertEqual(search('*** ```', db=self.db), [])

    def test_legacy_formatting_index_is_read_without_reimport(self):
        ready = copy.deepcopy(self.batch)
        ready['pages'][0]['fragments'][0].update(body='**книг**ообмен', end=True)
        self.load(ready)
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute('UPDATE chunks SET search_text=?', ('物质名词\n**книг**ообмен',))
            conn.commit()
        self.assertEqual(search('книгообмен', db=self.db)[0]['code'], 'm.1')
        with closing(sqlite3.connect(self.db)) as conn:
            self.assertIn('**книг**', conn.execute('SELECT search_text FROM chunks').fetchone()[0])

    def test_gap_and_unresolved_are_excluded(self):
        self.load()
        gap = copy.deepcopy(self.batch)
        gap['batch_id'] = 'b'
        gap['pages'][0].update(pdf_page=3, printed_page='3')
        gap['pages'][0]['fragments'][0].update(body='end', start=False, end=True)
        self.assertEqual(self.load(gap)['chunks'], {'incomplete': 1})
        unresolved = copy.deepcopy(self.batch)
        unresolved['batch_id'] = 'c'
        unresolved['pages'][0].update(pdf_page=4, unresolved=['source issue'])
        unresolved['pages'][0]['fragments'][0].update(code='m.2', start=True, end=True)
        self.load(unresolved)
        self.assertEqual(search('молоко', db=self.db), [])

    def test_wrong_source_and_boundaries_rollback(self):
        wrong = copy.deepcopy(self.batch)
        wrong['source_sha256'] = 'bad'
        with self.assertRaisesRegex(ValueError, 'different PDF'):
            self.load(wrong)
        self.load()
        bad = copy.deepcopy(self.batch)
        bad['batch_id'] = 'b'
        bad['pages'][0]['pdf_page'] = 2
        with self.assertRaisesRegex(ValueError, 'boundaries'):
            self.load(bad)
        with closing(sqlite3.connect(self.db)) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM batches').fetchone()[0], 1)

    def test_correction_requires_old_hash_and_preserves_revision(self):
        self.load()
        changed = copy.deepcopy(self.batch)
        changed['batch_id'] = 'correction'
        page = changed['pages'][0]
        page['expected_review_sha256'] = hashlib.sha256(json.dumps(self.batch['pages'][0], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        page['correction_reason'] = 'Visual recheck of original'
        page['fragments'][0].update(body='молоко́', end=True)
        self.assertEqual(self.load(changed)['corrected_pages'], 1)
        with closing(sqlite3.connect(self.db)) as conn:
            old = conn.execute('SELECT previous_json FROM page_revisions').fetchone()[0]
            self.assertIn('молоко́ 和 ве', old)
        changed['batch_id'] = 'stale'
        with self.assertRaisesRegex(ValueError, 'matching hash'):
            self.load(changed)
        self.assertEqual(search('молоко', db=self.db)[0]['body'], 'молоко́')


if __name__ == '__main__':
    unittest.main()
