import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_aspect_unnumbered_parallel import replay_language_span

class ParallelProjectionTests(unittest.TestCase):
    def setUp(self):
        self.raw='RU(汉语)';self.edit=dict(start=0,old=self.raw,new='RU(中文)',issue_id='fixture')
    def test_unchanged_russian_is_not_translated_or_changed(self):
        text,edits,proof=replay_language_span(self.raw,0,2,[self.edit]);self.assertEqual((text,edits),('RU',[]));self.assertEqual(proof[0]['source_edit'],self.edit);self.assertFalse(proof[0]['changed_text_inside_language_span'])
    def test_chinese_change_keeps_full_edit_proof(self):
        text,edits,proof=replay_language_span(self.raw,3,5,[self.edit]);self.assertEqual(text,'中文');self.assertEqual((edits[0]['start'],edits[0]['old'],edits[0]['new']),(3,'汉语','中文'));self.assertEqual(proof[0]['source_edit'],self.edit)
    def test_whole_group_uses_original_edit_without_projection(self):
        text,edits,proof=replay_language_span(self.raw,0,len(self.raw),[self.edit]);self.assertEqual(text,'RU(中文)');self.assertEqual(edits,[self.edit]);self.assertEqual(proof,[])
    def test_real_cross_language_change_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Changed text crosses'):replay_language_span(self.raw,3,5,[dict(start=0,old=self.raw,new='XX(中文)')])
    def test_cross_boundary_insertion_requires_review(self):
        with self.assertRaisesRegex(ValueError,'insertion'):replay_language_span('RU()',0,2,[dict(start=0,old='RU()',new='RU(x)')])
    def test_stale_old_text_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Stale'):replay_language_span(self.raw,3,5,[dict(start=0,old='XX(汉语)',new='XX(中文)')])
    def test_no_edit_keeps_exact_span(self):
        self.assertEqual(replay_language_span(self.raw,3,5,[]),('汉语',[],[]))

if __name__=='__main__':unittest.main()
