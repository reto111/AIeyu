"""Isolation, provenance, and retrieval-gate checks using synthetic sources."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import copy
from unittest.mock import patch

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import tonglun_reference as corpus
import tonglun_rag as rag


class TonglunReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        sources = {}
        for volume in (1, 2):
            sources[volume] = self.root / f'source{volume}.pdf'
            with pymupdf.open() as doc:
                for _ in range(3):
                    doc.new_page()
                doc.save(sources[volume])
        self.patches = [patch.object(corpus, 'WORK', self.root / 'work'),
                        patch.object(corpus, 'SOURCES', sources)]
        for p in self.patches:
            p.start()
        corpus.inventory()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def raw(self, volume, page=1, text='同页号测试'):
        image = corpus.volume_work(volume) / 'renders' / f'p{page:04d}.png'
        image.parent.mkdir(parents=True, exist_ok=True)
        image.write_bytes(b'image evidence')
        record = dict(volume=volume, pdf_page=page, printed_page=None,
                      source_sha256=corpus.file_sha256(corpus.SOURCES[volume]),
                      text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                      image_sha256=corpus.file_sha256(image), method='tesseract',
                      dpi=220, status='unreviewed', text=text)
        path = corpus.volume_work(volume) / 'raw' / f'p{page:04d}.json'
        corpus.dump(path, record)
        return path

    def review(self, volume, *, unresolved=False, complete=True):
        batch = dict(batch_id=f'v{volume}',
                     source_sha256=corpus.file_sha256(corpus.SOURCES[volume]), pages=[
            dict(pdf_page=1, printed_page='2', review_method='visual_comparison', fragments=[
                dict(code='chapter.1', title='语法意义', body='名词表示事物的语法意义。',
                     start=True, end=complete, unresolved=['待核'] if unresolved else [])])])
        path = self.root / f'batch{volume}.json'
        corpus.dump(path, batch)
        return corpus.import_batch(path, db=corpus.reviewed_db(volume),
                                   pdf=corpus.SOURCES[volume], title=corpus.source_title(volume), apply=True)

    def test_volume_page_keys_and_unreviewed_search_gate(self):
        self.raw(1)
        self.raw(2)
        corpus.build_corpus()
        with closing(sqlite3.connect(corpus.WORK / 'tonglun_corpus.sqlite')) as conn:
            self.assertEqual(conn.execute('SELECT volume,pdf_page FROM raw_pages ORDER BY volume').fetchall(), [(1, 1), (2, 1)])
        self.assertEqual(corpus.retrieve('同页号'), [])
        rows = corpus.retrieve('同页号', include_unreviewed=True)
        self.assertEqual([r['volume'] for r in rows], [1, 2])
        self.assertTrue(all(r['status'] == 'unreviewed' for r in rows))

    def test_cache_tampering_prevents_corpus_replacement(self):
        path = self.raw(1)
        corpus.build_corpus()
        db = corpus.WORK / 'tonglun_corpus.sqlite'
        before = corpus.file_sha256(db)
        record = json.loads(path.read_text(encoding='utf8'))
        record['text'] = 'tampered'
        corpus.dump(path, record)
        with self.assertRaisesRegex(ValueError, 'Text hash mismatch'):
            corpus.build_corpus()
        self.assertEqual(before, corpus.file_sha256(db))

    def test_source_and_image_changes_rejected(self):
        path = self.raw(1)
        record = json.loads(path.read_text(encoding='utf8'))
        record['source_sha256'] = 'wrong source'
        corpus.dump(path, record)
        with self.assertRaisesRegex(ValueError, 'Source mismatch'):
            corpus.build_corpus()
        self.raw(1)
        (corpus.volume_work(1) / 'renders/p0001.png').write_bytes(b'changed image')
        with self.assertRaisesRegex(ValueError, 'Image hash mismatch'):
            corpus.build_corpus()

    def test_reviewed_sources_keep_volume_and_title(self):
        self.review(1)
        self.review(2)
        hits = corpus.retrieve('语法意义')
        self.assertEqual([h['volume'] for h in hits], [1, 2])
        self.assertIn('上册', hits[0]['citation'])
        self.assertIn('下册', hits[1]['citation'])

    def test_incomplete_and_unresolved_never_retrieved(self):
        self.review(1, complete=False)
        self.review(2, unresolved=True)
        self.assertEqual(corpus.retrieve('语法意义'), [])

    def test_cached_page_is_not_reocrd_and_config_changes_rejected(self):
        self.raw(1)
        fingerprint = corpus.file_sha256(corpus.SOURCES[1])
        with patch.object(corpus.subprocess, 'run', side_effect=AssertionError('unexpected OCR')):
            corpus.extract_one(1, 1, fingerprint, 220)
        with self.assertRaisesRegex(ValueError, 'configuration differs'):
            corpus.extract_one(1, 1, fingerprint, 300)

    def test_rag_multi_volume_identity_quotes_and_budget(self):
        self.review(1)
        self.review(2)
        packet = rag.prepare('本书怎样解释语法意义？', '语法意义')
        self.assertEqual([s['volume'] for s in packet['sources']], [1, 2])
        response = dict(status='answered', claims=[dict(text_zh='测试说明', citations=[
            dict(source_id=s['source_id'], quote='名词表示事物的语法意义。') for s in packet['sources']])])
        checked = rag.validate(packet, response)
        self.assertEqual(checked['status'], 'citations_checked')
        self.assertEqual([c['volume'] for c in checked['claims'][0]['citations']], [1, 2])
        changed = copy.deepcopy(response)
        changed['claims'][0]['citations'][0]['quote'] = '来源中不存在的文本。'
        with self.assertRaisesRegex(ValueError, 'absent'):
            rag.validate(packet, changed)
        changed_packet = copy.deepcopy(packet)
        changed_packet['sources'][0]['volume'] = 2
        with self.assertRaisesRegex(ValueError, 'altered'):
            rag.validate(changed_packet, response)
        self.assertEqual(rag.prepare('问题', '语法意义', max_context_chars=1)['status'], 'context_over_budget')
        self.assertEqual(rag.prepare('问题', '不存在的术语')['status'], 'no_evidence')

    def test_rag_rechecks_source_and_review_after_prepare(self):
        self.review(1)
        packet = rag.prepare('问题', '语法意义')
        with closing(sqlite3.connect(corpus.reviewed_db(1))) as conn:
            conn.execute("UPDATE chunks SET status='unresolved',notes='[\"new issue\"]'")
            conn.commit()
        with self.assertRaisesRegex(ValueError, 'not ready'):
            rag.validate(packet, dict(status='insufficient_evidence', message_zh='证据不足'))


if __name__ == '__main__':
    unittest.main()
