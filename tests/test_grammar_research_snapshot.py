from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from grammar_reference import dump, file_sha256, import_batch
from export_grammar_research_snapshot import export_snapshot, read_jsonl, verify_package, write_jsonl
from evaluate_grammar_retrieval import evaluate
from grammar_rag import text_hash
from replay_grammar_research_snapshot import replay


class GrammarResearchSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.pdf, self.db = self.root/'source.pdf', self.root/'grammar.sqlite'
        with pymupdf.open() as doc:
            for _ in range(2):
                doc.new_page()
            doc.save(self.pdf)
        batch = dict(batch_id='fixture', source_sha256=file_sha256(self.pdf), pages=[
            dict(pdf_page=1, printed_page='9', review_method='visual_comparison',fragments=[
                dict(code='m.1',title='词根',body='中文与**ё、и́**原印。',start=True,end=True)]),
            dict(pdf_page=2, printed_page='10', review_method='visual_comparison',fragments=[
                dict(code='m.2',title='隔离节',body='原书疑形保留。',start=True,end=True,unresolved=['待核'])])])
        dump(self.root/'batch.json',batch)
        import_batch(self.root/'batch.json',db=self.db,pdf=self.pdf,apply=True)
        self.output=self.root/'package'
        self.before=file_sha256(self.db)

    def tearDown(self):
        self.temp.cleanup()

    def export(self):
        return export_snapshot(self.output,db=self.db)

    def rehash(self,name):
        path=self.output/'manifest.json'
        m=json.loads(path.read_text(encoding='utf8'))
        m['files'][name]=file_sha256(self.output/name)
        dump(path,m)

    def test_preserves_body_provenance_and_excludes_unresolved(self):
        result=self.export()
        self.assertEqual(result['counts']['retrieval_ready'],1)
        self.assertEqual(result['counts']['excluded'],1)
        ready=read_jsonl(self.output/'retrieval_ready.jsonl')
        self.assertEqual(ready[0]['body'],'中文与**ё、и́**原印。')
        self.assertEqual(ready[0]['pdf_pages'],[1])
        self.assertEqual(ready[0]['printed_pages'],['9'])
        self.assertEqual(len(ready[0]['page_evidence']),1)
        self.assertTrue(read_jsonl(self.output/'excluded_sections.jsonl')[0]['notes'])
        self.assertEqual(file_sha256(self.db),self.before)
        export_snapshot(self.root/'second',db=self.db)
        for name in ('pages','sections','retrieval_ready','excluded_sections','batches'):
            self.assertEqual((self.output/(name+'.jsonl')).read_bytes(),(self.root/'second'/(name+'.jsonl')).read_bytes())

    def test_verify_is_portable_without_original_pdf(self):
        self.export()
        self.pdf.rename(self.root/'moved.pdf')
        self.output.rename(self.root/'relocated')
        self.assertEqual(verify_package(self.root/'relocated')['status'],'verified')

    def test_blocks_overwrite_and_detects_file_tampering(self):
        self.export()
        with self.assertRaises(FileExistsError):
            self.export()
        with (self.output/'retrieval_ready.jsonl').open('a',encoding='utf8') as f:
            f.write('{}\n')
        with self.assertRaises(ValueError):
            verify_package(self.output)
        self.assertEqual(file_sha256(self.db),self.before)

    def test_detects_changed_provenance_even_if_export_hash_is_updated(self):
        self.export()
        rows=read_jsonl(self.output/'sections.jsonl')
        rows[0]['printed_pages']=['wrong']
        write_jsonl(self.output/'sections.jsonl',rows)
        self.rehash('sections.jsonl')
        with self.assertRaises(ValueError):
            verify_package(self.output)

    def test_detects_isolated_section_in_retrieval_even_after_rehash(self):
        self.export()
        rows=read_jsonl(self.output/'sections.jsonl')
        write_jsonl(self.output/'retrieval_ready.jsonl',rows)
        self.rehash('retrieval_ready.jsonl')
        with self.assertRaises(ValueError):
            verify_package(self.output)

    def test_packaged_entry_does_not_create_cache_or_break_inventory(self):
        self.export()
        script=self.output/'source_code/scripts/export_grammar_research_snapshot.py'
        result=subprocess.run([sys.executable,'-X','utf8',str(script),'verify',str(self.output)],
                              capture_output=True,text=True,encoding='utf8')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(list(self.output.rglob('*.pyc')))
        self.assertEqual(verify_package(self.output)['status'],'verified')

    def test_snapshot_replay_requires_frozen_source_binding(self):
        self.export()
        scripts=Path(__file__).resolve().parents[1]/'scripts'
        frozen=dict(frozen_at='test',database_sha256=self.before,
            implementation_sha256=file_sha256(scripts/'grammar_question_search.py'),
            rag_implementation_sha256=file_sha256(scripts/'grammar_rag.py'),limit=3,max_context_chars=16000,
            cases=[dict(case_id='one',kind='single',question='词根是什么？',expected_codes=['m.1'],
                forbidden_codes=[],gold_sources=[dict(code='m.1',status='ready',body_sha256=text_hash('中文与**ё、и́**原印。'))])],limits='fixture')
        path=self.root/'cases.json'
        dump(path,frozen)
        result=evaluate(path,self.root/'result.json',db=self.output/'grammar_reference.sqlite',snapshot=self.output)
        self.assertEqual(result['external_api_calls'],0)
        self.pdf.rename(self.root/'moved.pdf')
        offline_path=self.root/'offline.json'
        replay(self.output,path,offline_path)
        offline=json.loads(offline_path.read_text(encoding='utf8'))
        online=json.loads((self.root/'result.json').read_text(encoding='utf8'))
        self.assertEqual(offline['pdf_files_opened'],0)
        self.assertEqual(offline['records'][0]['sources'],online['records'][0]['packet']['sources'])
        self.assertEqual(len(offline['records'][0]['sources']),1)
        with self.assertRaises(ValueError):
            replay(self.output,path,self.output/'invalid.json')
        frozen['database_sha256']='0'*64
        dump(path,frozen)
        with self.assertRaises(ValueError):
            evaluate(path,self.root/'bad-result.json',db=self.output/'grammar_reference.sqlite',snapshot=self.output)


if __name__=='__main__':
    unittest.main()
