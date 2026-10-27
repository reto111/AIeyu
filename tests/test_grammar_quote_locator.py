from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from grammar_quote_locator import locate,locate_in_trace

class QuoteLocatorTests(unittest.TestCase):
    def test_unchanged_quote_is_literal_even_in_edited_section(self):
        result=locate('morphology.103','不定式没有时间、式、人称等语法意义，但有体的区别。')
        self.assertEqual(result['source_content_kind'],'editorial_research')
        self.assertTrue(result['quote_found'])
        self.assertTrue(all(h['literal_in_original_at_this_span']for h in result['occurrences']))
        self.assertTrue(all(h['pdf_pages']for h in result['occurrences']))

    def test_inserted_history_not_falsely_called_original(self):
        result=locate('morphology.103','-кть、-гть（-кти/-гти）')
        self.assertTrue(result['quote_found'])
        self.assertTrue(all(h['provenance_kind']=='editorial_derived_span'for h in result['occurrences']))

    def test_repeated_table_row_does_not_pick_one_page(self):
        result=locate('morphology.075','|四格|同一格|同一格|同一格|')
        self.assertTrue(result['ambiguous'])
        self.assertGreater(len(result['occurrences']),1)
        self.assertGreater(len({tuple(h['pdf_pages'])for h in result['occurrences']}),1)

    def test_wrong_accent_and_markdown_stay_unmatched(self):
        self.assertFalse(locate('syntax.119','对应ска́зала')['quote_found'])
        self.assertFalse(locate('syntax.119','“Она **удиви́лась и сказа́ла**,”下分两支')['quote_found'])

    def test_deleted_gap_is_derived_without_inserted_characters(self):
        trace={'normalized_body':'abc','raw_normalized_body':'aXbc',
               'labels':[(frozenset([10]),i,i)for i in [0,2,3]],
               'source':{'code':'fixture','body_sha256':'fixture','content_kind':'editorial_research','pdf_pages':[10]},
               'pages':[{'pdf_page':10,'printed_page':'1','page_review_sha256':'fixture'}]}
        result=locate_in_trace(trace,'abc')['occurrences'][0]
        self.assertFalse(result['contains_replacement_characters'])
        self.assertFalse(result['literal_in_original_at_this_span'])

    def test_derived_boundary_anchor_keeps_both_pages(self):
        trace={'normalized_body':'xyz','raw_normalized_body':'abc',
               'labels':[(frozenset([10,11]),None,None)]*3,
               'source':{'code':'fixture','body_sha256':'fixture','content_kind':'editorial_research','pdf_pages':[10,11]},
               'pages':[{'pdf_page':p,'printed_page':str(p-9),'page_review_sha256':'fixture'}for p in [10,11]]}
        result=locate_in_trace(trace,'xyz')['occurrences'][0]
        self.assertEqual(result['pdf_pages'],[10,11])
        self.assertTrue(result['contains_replacement_characters'])

    def test_excluded_appendix_not_locatable(self):
        with self.assertRaises(ValueError):locate('morphology.declension_tables','第一格')

if __name__=='__main__':unittest.main()
