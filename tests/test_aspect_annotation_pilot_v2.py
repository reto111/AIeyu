import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_aspect_annotation_pilot_v2 as model

class AnnotationConstraints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items=json.loads((model.WORK/'reviews/semantic_annotation_multiaxis_input_20261022_001.json').read_text('utf8'))['annotations']

    def test_ambiguous_joint_analyses_keep_opposed_aspect_and_tense(self):
        x=self.items[5];model.validate_labels(x)
        self.assertEqual([(a['lemma'],a['aspect'],a['grammatical_tense'])for a in x['form_analyses']],[('узнавать','imperfective','present'),('узнать','perfective','future')])

    def test_future_auxiliary_does_not_assign_time_to_infinitive(self):
        x=copy.deepcopy(self.items[8]);model.validate_labels(x)
        self.assertEqual(x['construction']['tense'],'future')
        x['form_analyses'][0]['morphological_tense']='nonpast'
        with self.assertRaisesRegex(ValueError,'inherit auxiliary'):model.validate_labels(x)

    def test_command_cannot_certify_performed_event(self):
        x=copy.deepcopy(self.items[14]);x['semantic_axes']['event_realization']['value']='presented_as_occurred'
        with self.assertRaisesRegex(ValueError,'certify execution'):model.validate_labels(x)

    def test_chinese_marker_cannot_become_russian_lexical_aspect(self):
        x=copy.deepcopy(self.items[18]);x['form_analyses'][0]['aspect']='perfective'
        with self.assertRaisesRegex(ValueError,'Russian morphological'):model.validate_labels(x)

    def test_each_axis_must_name_existing_source_evidence(self):
        x=copy.deepcopy(self.items[0]);x['semantic_axes']['reference_result_state']['basis']=[999]
        with self.assertRaisesRegex(ValueError,'Missing axis evidence'):model.validate_labels(x)

    def test_result_cancellation_and_relevance_can_coexist(self):
        x=self.items[9];model.validate_labels(x)
        self.assertEqual(x['semantic_axes']['reference_result_state']['value'],'cancelled_explicitly')
        self.assertEqual(x['semantic_axes']['consequence_relevance']['value'],'relevant_in_source_reading')

if __name__=='__main__':unittest.main()
