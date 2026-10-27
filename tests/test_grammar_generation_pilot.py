import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_grammar_generation_pilot as pilot
import grammar_question_search as baseline
import grammar_editorial_search_candidate as candidate

class GrammarPilotIntegrityTests(unittest.TestCase):
 def test_frozen_inputs_and_balanced_contexts(self):
  manifest=json.loads((pilot.OUT/'freeze_manifest.json').read_text(encoding='utf-8'))
  for rel,h in manifest['files'].items():self.assertEqual(pilot.digest(pilot.OUT/rel),h,rel)
  requests=sorted((pilot.OUT/'requests').glob('*.json'));self.assertEqual(len(requests),20)
  first={'rag':0,'control':0}
  for index in range(0,20,2):
   first[requests[index].stem.split('_')[-1]]+=1
   pair=[json.loads(p.read_text(encoding='utf-8'))for p in requests[index:index+2]]
   self.assertEqual(pair[0]['messages'][0],pair[1]['messages'][0])
   payloads=[json.loads(p['messages'][1]['content'])for p in pair]
   self.assertEqual(payloads[0]['question'],payloads[1]['question'])
   self.assertEqual(sum(bool(p['retrieved_sources'])for p in payloads),1)
  self.assertEqual(first,{'rag':5,'control':5})
 def test_completed_run_cannot_send_twenty_more(self):
  self.assertEqual(len(list((pilot.OUT/'attempts').glob('*.json'))),20)
  with patch('urllib.request.urlopen',side_effect=AssertionError('No further requests allowed')) as network:
   pilot.run()
  network.assert_not_called()
 def test_candidate_does_not_modify_baseline_topics(self):
  self.assertNotIn('不能使用副动词的情况',baseline.TOPICS)
  q='副动词动作属于不同主体时能使用吗？'
  before=baseline.question_terms(q)
  self.assertIn('不能使用副动词的情况',candidate.expand_question(q)[1])
  candidate.lexical.question_terms(candidate.expand_question(q)[0])
  self.assertEqual(baseline.question_terms(q),before)
 def test_candidate_avoids_unrelated_daily_language(self):
  for q in ['临时工长期做卡片设计，需要多少钱？','没有我或你的照片，该如何打印？','复数格式文件不知道谁做的，能打开吗？']:
   self.assertEqual(candidate.expand_question(q)[1],[])
 def test_audit_keeps_failed_quotes(self):
  audit=json.loads((pilot.OUT/'audit_001.json').read_text(encoding='utf-8'))
  self.assertEqual(audit['attempts'],20)
  self.assertEqual(audit['groups']['rag']['mechanically_valid_answered'],6)
  self.assertEqual(audit['citation_summary']['passes_frozen_quote_rule'],36)
  self.assertTrue(audit['source_database_unchanged'])

if __name__=='__main__':unittest.main()
