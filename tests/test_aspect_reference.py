from contextlib import closing
import copy
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import pymupdf
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import aspect_reference as aspect
import grammar_reference as grammar


class AspectReferenceTests(unittest.TestCase):
    def test_core_does_not_change_original_grammar_defaults(self):
        self.assertIsNot(aspect.core,grammar)
        self.assertNotEqual(aspect.WORK,grammar.WORK)
        self.assertNotEqual(aspect.DB,grammar.DB)
        self.assertEqual(grammar.PDF.name,'Russian_grammar_reference_scan.pdf')
        self.assertEqual(aspect.core.WORK,aspect.WORK)

    def test_isolated_source_preview_import_citation_and_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            pdf=root/'source.pdf'
            with pymupdf.open() as doc:
                doc.new_page()
                doc.save(pdf)
            db=root/'aspect.sqlite'
            batch=dict(batch_id='sample',source_sha256=grammar.file_sha256(pdf),pages=[
                dict(pdf_page=1,printed_page='1',review_method='visual_comparison',fragments=[
                    dict(code='aspect.1',title='体的对立',body='完成体和未完成体的不同表述。',start=True,end=True)])])
            candidate=root/'sample.json'
            grammar.dump(candidate,batch)
            with patch.multiple(aspect,PDF=pdf,DB=db):
                self.assertFalse(aspect.import_batch(candidate)['applied'])
                self.assertFalse(db.exists())
                aspect.import_batch(candidate,True)
                rows=aspect.core.search('完成体',db=db)
                self.assertIn(aspect.TITLE,rows[0]['citation'])
                self.assertEqual(rows[0]['source_sha256'],grammar.file_sha256(pdf))
                self.assertEqual(aspect.import_batch(candidate,True)['result'],'already_imported')
                old=grammar.file_sha256(db)
                batch['source_sha256']='wrong'
                grammar.dump(candidate,batch)
                with self.assertRaisesRegex(ValueError,'different PDF'):
                    aspect.import_batch(candidate,True)
                self.assertEqual(old,grammar.file_sha256(db))

    def test_ocr_resume_rejects_foreign_page_before_render(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            pdf=root/'source.pdf'
            with pymupdf.open() as doc:
                doc.new_page()
                doc.save(pdf)
            grammar.dump(root/'ocr/p0001.json',dict(pdf_page=1,source_sha256='foreign'))
            with patch.multiple(aspect,PDF=pdf,WORK=root),patch.object(aspect.core,'render_page') as render:
                with self.assertRaisesRegex(ValueError,'another source/page'):
                    aspect.ocr(1,1)
                render.assert_not_called()


if __name__=='__main__':
    unittest.main()
