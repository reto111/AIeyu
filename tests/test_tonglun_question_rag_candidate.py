import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import tonglun_question_rag_candidate as candidate
import tonglun_rag as rag
from tests import test_tonglun_reference as reference_tests


class TonglunQuestionCandidateTests(unittest.TestCase):
    def setUp(self):
        self.fixture = reference_tests.TonglunReferenceTests()
        self.fixture.setUp()

    def tearDown(self):
        self.fixture.tearDown()

    def test_longest_topic_consumes_completed_aspect_substring(self):
        forms = candidate.title_terms(['完成体 / 未完成体 / 疑问—关系代词'])
        self.assertEqual(candidate.extract_terms('未完成体是什么？', forms), ['未完成体'])
        self.assertEqual(candidate.extract_terms('疑问关系代词有什么作用？', forms), ['疑问—关系代词'])

    def test_russian_words_keep_yo_and_complete_word_boundaries(self):
        self.assertEqual(candidate.term_count('он',candidate.norm('слон он'),{}),1)
        self.assertEqual(candidate.term_count('поёт',candidate.norm('поет'),{}),0)

    def test_prepared_packet_validates_and_other_volume_isolated(self):
        for volume in (1,2):
            self.fixture.raw(volume)
            self.fixture.review(volume, unresolved=volume==2)
        packet=candidate.prepare('语法意义是什么？')
        self.assertEqual(packet['status'],'prepared')
        self.assertEqual([x['volume'] for x in packet['sources']],[1])
        checked=rag.validate(packet,dict(status='answered',claims=[dict(text_zh='工程引句检查',citations=[dict(source_id='T1',quote='名词表示事物的语法意义。')])]))
        self.assertEqual(checked['status'],'citations_checked')
        self.assertEqual(candidate.prepare('语法意义是什么？',max_context_chars=1)['status'],'context_over_budget')

    def test_unrelated_empty_and_invalid_inputs(self):
        for volume in (1,2):
            self.fixture.raw(volume);self.fixture.review(volume)
        self.assertEqual(candidate.prepare('天空为什么这么蓝？')['status'],'no_evidence')
        for question in ('', None, 'a'*2001):
            with self.assertRaises(ValueError):candidate.prepare(question)
        with self.assertRaises(ValueError):candidate.prepare('语法意义',limit=0)


if __name__ == '__main__':unittest.main()
