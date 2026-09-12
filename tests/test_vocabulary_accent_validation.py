import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from import_vocabulary_learning import check_accent


class AccentValidationTests(unittest.TestCase):
    def test_fixed_particle_and_existing_suffixes(self):
        for word in ('всё-таки', 'кто-нибудь', 'како́й-либо', 'кто-то'):
            check_accent(word)

    def test_no_general_exemption_for_taki_or_missing_accents(self):
        for word in ('все-таки', 'сло́во-таки', 'молоко', 'сло́во-слово'):
            with self.subTest(word=word), self.assertRaises(ValueError):
                check_accent(word)

    def test_invalid_accent_placement_still_rejected(self):
        for word in ('́слово', 'с́лово', 'сло́во́'):
            with self.subTest(word=word), self.assertRaises(ValueError):
                check_accent(word)


if __name__ == '__main__':
    unittest.main()
