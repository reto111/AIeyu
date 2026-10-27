import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from aspect_annotation_agreement import nominal_agreement

class NominalAgreementTests(unittest.TestCase):
    def test_empty_templates_are_not_perfect_agreement(self):
        r=nominal_agreement(['',''],['','']);self.assertEqual(r['paired'],0);self.assertIsNone(r['agreement']);self.assertIsNone(r['kappa'])

    def test_known_nontrivial_kappa(self):
        r=nominal_agreement(['A','A','B','B'],['A','B','B','B']);self.assertEqual(r['agreement'],.75);self.assertEqual(r['expected_agreement'],.5);self.assertEqual(r['kappa'],.5)

    def test_constant_marginals_leave_kappa_undefined(self):
        r=nominal_agreement(['unknown','unknown'],['unknown','unknown']);self.assertEqual(r['agreement'],1);self.assertIsNone(r['kappa']);self.assertEqual(r['undefined_reason'],'no_marginal_variation')

    def test_unknown_is_category_but_missing_is_excluded(self):
        r=nominal_agreement(['unknown','','A'],['A','B','A']);self.assertEqual(r['paired'],2);self.assertEqual(r['left_labels']['unknown'],1);self.assertEqual(r['agreement'],.5)

    def test_kappa_symmetry_and_length_validation(self):
        a=['A','A','B','unknown'];b=['B','A','A','unknown'];self.assertEqual(nominal_agreement(a,b)['kappa'],nominal_agreement(b,a)['kappa'])
        with self.assertRaises(ValueError):nominal_agreement(a,b[:-1])

    def test_official_documentation_numeric_example(self):
        # Public primary documentation gives kappa=0.6875 for these labels:
        # https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html
        a=['negative','positive','negative','neutral','positive'];b=['negative','positive','negative','neutral','negative']
        self.assertAlmostEqual(nominal_agreement(a,b)['kappa'],.6875)

if __name__=='__main__':unittest.main()
