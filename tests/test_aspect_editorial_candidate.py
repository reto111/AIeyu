from pathlib import Path
import sys
import sqlite3
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import aspect_candidate_rag as rag
from build_aspect_editorial_candidate import replay

class AspectCandidateTests(unittest.TestCase):
    def test_simultaneous_offsets_preserve_unedited_stress_and_yo(self):
        raw='ё, до́м; abc; й.'
        edits=[dict(start=9,old='abc',new='longer text'),dict(start=0,old='ё',new='е')]
        self.assertEqual(replay(raw,edits),'е, до́м; longer text; й.')

    def test_reject_conflicting_old_value(self):
        with self.assertRaisesRegex(ValueError,'span'):
            replay('abc',[dict(start=0,old='xyz',new='abc')])

    def test_reject_overlapping_edits(self):
        with self.assertRaisesRegex(ValueError,'span'):
            replay('abcdef',[dict(start=0,old='abc',new='x'),dict(start=2,old='cde',new='y')])

    def test_reject_empty_old_value(self):
        with self.assertRaisesRegex(ValueError,'span'):
            replay('abc',[dict(start=0,old='',new='unbounded insertion')])

    def test_longest_topic_does_not_conflate_aspect_pair(self):
        terms=rag.question_terms('未完成体的概括事实意义有什么特点？')
        self.assertIn('未完成体',terms)
        self.assertNotIn('完成体',terms)

    def test_search_ignores_stress_but_preserves_yo_and_short_i(self):
        self.assertEqual(rag.normal('ЁЖИК й до́м'),'ёжик й дом')
        self.assertNotEqual(rag.normal('ёлка'),rag.normal('елка'))

    def test_russian_token_boundaries(self):
        self.assertEqual(rag.occurrences('по','пойти по полю'),1)
        self.assertEqual(rag.occurrences('не','нет не понял'),1)

    def test_document_contrasting_labels_do_not_overlap(self):
        self.assertEqual(rag.occurrences('完成体','未完成体 完成体'),1)
        self.assertEqual(rag.occurrences('界限动词','无界限动词 界限动词'),1)

    def test_topical_surface_variants_count_once(self):
        self.assertEqual(rag.occurrences('界限性','无界限动词'),1)
        self.assertEqual(rag.occurrences('俄汉对比','俄、汉语'),1)

    def test_unrelated_prompt_has_no_topics(self):
        self.assertEqual(rag.question_terms('如何修改我的登录密码？'),[])

    def test_passage_search_never_uses_withheld_or_implicit_candidate(self):
        c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
        self.addCleanup(c.close)
        c.execute('create table aspect_candidate_sections(code text,title text,body text,state text)')
        c.executemany('insert into aspect_candidate_sections values(?,?,?,?)',[
            ('allowed','未完成体过去时','未完成体过去时有概括事实意义。','original_source_ready'),
            ('candidate','未完成体过去时的概括事实意义','未完成体过去时的概括事实意义。','model_editorial_candidate'),
            ('blocked','未完成体过去时的概括事实意义','未完成体过去时的概括事实意义。'*30,'withheld')])
        original,_=rag.search_question_passages(c,'未完成体过去时的概括事实意义是什么？')
        expanded,_=rag.search_question_passages(c,'未完成体过去时的概括事实意义是什么？',True)
        self.assertEqual([x['code']for x in original],['allowed'])
        self.assertEqual({x['code']for x in expanded},{'allowed','candidate'})

    def test_passage_search_does_not_use_character_coincidence_as_topic(self):
        c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
        self.addCleanup(c.close)
        c.execute('create table aspect_candidate_sections(code text,title text,body text,state text)')
        c.execute('insert into aspect_candidate_sections values(?,?,?,?)',('a','背景介绍','怎样给图片换成蓝色背景？','original_source_ready'))
        self.assertEqual(rag.search_question_passages(c,'怎样给图片换成蓝色背景？',True)[0],[])

    def test_passage_windows_cover_end_without_changing_source(self):
        body='开头'+('俄语未完成体。'*200)+'正文末尾'
        windows=rag.section_passages(body)
        self.assertTrue(windows[0].startswith('开头'))
        self.assertTrue(windows[-1].endswith('正文末尾'))
        self.assertTrue(all(len(x)<=700 for x in windows))
        self.assertTrue(all(x in body for x in windows))

if __name__=='__main__':unittest.main()
