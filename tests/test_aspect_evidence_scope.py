import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import aspect_evidence_scope_candidate as scope

class ScopeCandidateTests(unittest.TestCase):
    def test_personal_fact_request_never_prepares_book_prompt(self):
        with patch.object(scope.rag,'prepare',side_effect=AssertionError('Book retrieval called')):
            p=scope.prepare('请从我的后台查询俄语成绩。')
        self.assertEqual(p['status'],'needs_external_evidence');self.assertEqual(p['sources'],[]);self.assertIsNone(p['prompt_package'])

    def test_quoted_price_example_keeps_language_analysis_route(self):
        p=scope.classify('分析“课程今天多少钱？”这个假想问句的未完成体用法。')
        self.assertEqual(p['route'],'language_analysis');self.assertTrue(p['quoted_examples_masked'])

    def test_mixed_request_puts_limitation_inside_actual_prompt_package(self):
        record=dict(status='prepared',sources=[dict(code='test',body='unchanged')],prompt_package=dict(system_prompt='original',user_payload=dict(question='original')))
        with patch.object(scope.rag,'prepare',return_value=record):p=scope.prepare('解释完成体，再查询我的成绩。')
        self.assertEqual(p['status'],'partial_theory_evidence');self.assertIn('没有账号',p['prompt_package']['system_prompt']);self.assertEqual(p['sources'][0]['body'],'unchanged')

    def test_russian_corpus_count_needs_data(self):
        self.assertEqual(scope.classify('Сколько в НКРЯ примеров совершенного вида за 2025 год?')['route'],'external_facts_required')

if __name__=='__main__':unittest.main()
