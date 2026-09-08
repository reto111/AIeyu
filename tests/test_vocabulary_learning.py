import json
import shutil
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import serve_student_app as app
import import_vocabulary_learning as importer
import vocabulary_learning as learning


class VocabularyLearningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.path = self.root / 'test.sqlite'
        with closing(sqlite3.connect(ROOT / 'database/russian_ai_tutor.sqlite')) as source:
            with closing(sqlite3.connect(self.path)) as target:
                source.backup(target)
        self.mock = patch.object(app, 'DB_PATH', self.path)
        self.mock.start()
        with app.db() as conn:
            conn.execute('DELETE FROM vocabulary_learning_annotations')
            self.user = conn.execute("INSERT INTO users(display_name) VALUES ('word-level-test')").lastrowid
            self.other = conn.execute("INSERT INTO users(display_name) VALUES ('word-isolation-test')").lastrowid
        importer.apply_catalog(self.path, apply=True, backup_dir=self.root / 'backups')

    def tearDown(self):
        self.mock.stop()
        self.temp.cleanup()

    def test_grade_register_and_existing_account_defaults(self):
        credentials = dict(display_name='year-four-new', password='1234abcd', student_year=4)
        self.assertFalse(app.api_register(credentials)['authenticated'])
        login, _ = app.api_login(credentials)
        status = app.api_word_status(login['user']['id'], 'GENERAL', 'GENERAL')
        self.assertEqual(status['learning_profile']['student_year'], 4)
        self.assertEqual(status['learning_profile']['starting_stage'], 4)
        self.assertEqual(app.api_word_status(self.other, 'GENERAL')['learning_profile']['current_stage'], 1)
        with self.assertRaises(ValueError):
            app.api_register(dict(credentials, display_name='bad-grade', student_year=5))

    def test_beginner_range_stress_and_no_harder_fallback(self):
        payload = app.api_word_session(dict(user_id=self.user, exam_system='GENERAL', count=50))
        self.assertEqual(payload['count'], 50)
        self.assertEqual(len({w['word'] for w in payload['words']}), 50)
        with app.db() as conn:
            for word in payload['words']:
                self.assertTrue(word['accent'])
                self.assertEqual(conn.execute('SELECT stage FROM vocabulary_learning_annotations WHERE vocabulary_item_id=?',
                                             (word['vocabulary_item_id'],)).fetchone()[0], 1)
            conn.execute('DELETE FROM vocabulary_learning_annotations WHERE stage=1')
        self.assertEqual(app.api_word_session(dict(user_id=self.user, exam_system='GENERAL'))['count'], 0)

    def test_review_pool_shares_same_record_with_exam_not_other_user(self):
        word_id = 10836
        reply = app.api_word_review(dict(user_id=self.user, exam_system='GENERAL', vocabulary_item_id=word_id, result='fuzzy'))
        self.assertEqual(reply['word']['accent'], 'чита́ть')
        self.assertEqual(reply['word']['aspect_partner'], 'прочита́ть')
        self.assertEqual(app.api_word_review_pool(self.user, exam_system_code='GENERAL')['total'], 1)
        self.assertEqual(app.api_word_review_pool(self.user, exam_system_code='TEM4_RU', level_code='TEM4')['total'], 1)
        self.assertEqual(app.api_word_review_pool(self.other, exam_system_code='GENERAL')['total'], 0)
        # Instant review includes fuzzy words not due yet.
        session = app.api_word_session(dict(user_id=self.user, exam_system='GENERAL', mode='review'))
        self.assertEqual(session['words'][0]['vocabulary_item_id'], word_id)
        app.api_word_review(dict(user_id=self.user, exam_system='GENERAL', vocabulary_item_id=word_id, result='known'))
        self.assertEqual(app.api_word_review_pool(self.user, exam_system_code='GENERAL')['total'], 0)

    def test_unknown_daily_fuzzy_two_days_and_known_none(self):
        from datetime import datetime
        for result, days in [('unknown',1), ('fuzzy',2), ('known',None)]:
            reply = app.api_word_review(dict(user_id=self.user, exam_system='GENERAL', vocabulary_item_id=10836, result=result))
            if days is None:
                self.assertIsNone(reply['next_review_at'])
            else:
                delta = datetime.fromisoformat(reply['next_review_at']) - datetime.now()
                self.assertAlmostEqual(delta.total_seconds()/86400, days, places=3)

    def test_stage_settings_and_grade_are_not_mastery(self):
        app.api_word_preferences(dict(user_id=self.user, starting_stage=3, student_year=3))
        status = app.api_word_status(self.user, 'GENERAL')
        self.assertEqual(status['learning_profile']['current_stage'], 3)
        self.assertTrue(all(s['known'] == 0 for s in status['learning_profile']['stages']))
        with self.assertRaises(ValueError):
            app.api_word_review(dict(user_id=self.other, exam_system='GENERAL', vocabulary_item_id=3924, result='known'))
        self.assertEqual(app.api_word_status(self.other, 'GENERAL')['learning_profile']['current_stage'], 1)

    def test_progressive_threshold_requires_pool_and_real_known_words(self):
        rows = [dict(stage=1, progress_status='known' if i<15 else None) for i in range(20)]
        rows.append(dict(stage=2, progress_status=None))
        with app.db() as conn:
            self.assertEqual(learning.learning_profile(conn, self.user, rows)['current_stage'], 1)
            rows[15]['progress_status'] = 'known'
            self.assertEqual(learning.learning_profile(conn, self.user, rows)['current_stage'], 2)
            rows.extend(dict(stage=1, progress_status=None) for _ in range(80))
            self.assertEqual(learning.learning_profile(conn, self.user, rows)['current_stage'], 2)

    def test_import_idempotence_source_key_and_conflict(self):
        result = importer.apply_catalog(self.path, apply=True, backup_dir=self.root/'backups')
        self.assertEqual(result['inserted'], 0)
        self.assertEqual(result['skipped'], 200)
        # Display-only IDs in the patch need not equal server IDs.
        data = json.loads(importer.PATCH.read_text(encoding='utf-8'))
        for record in data['records']:
            record['id'] += 100000
        alternative = self.root/'remapped.json'
        alternative.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        self.assertEqual(importer.apply_catalog(self.path, alternative)['validated'], 200)
        with app.db() as conn:
            conn.execute("UPDATE vocabulary_items SET meaning_zh='后续人工编辑' WHERE id=10836")
        with self.assertRaises(ValueError):
            importer.apply_catalog(self.path, apply=True, backup_dir=self.root/'backups')
        self.assertNotIn(10836, [r['vocabulary_item_id'] for r in app.api_word_session(
            dict(user_id=self.user, exam_system='GENERAL', count=50))['words']])

    def test_source_confusion_and_yo_are_local_corrections(self):
        with app.db() as conn:
            for word_id, expected in [(8560,'ка́ша'),(8449,'иде́я'),(8734,'лёгкий')]:
                row = conn.execute('SELECT * FROM vocabulary_items WHERE id=?',(word_id,)).fetchone()
                reviewed = learning.annotation(conn, row)
                self.assertEqual(reviewed['accent'], expected)
            self.assertIn('粥', learning.annotation(conn, conn.execute('SELECT * FROM vocabulary_items WHERE id=8560').fetchone())['core_meaning_zh'])

    def test_stressed_selection_uses_reviewed_meaning_without_external_ai(self):
        with patch.object(app, 'deepseek_selection_translation', side_effect=AssertionError('no external call')):
            result = app.api_translate_selection(dict(user_id=self.user, selected_text='ка́ша', exam_system='GENERAL'))
            self.assertIn('粥', result['meaning_zh'])
            self.assertNotIn('咳嗽', result['meaning_zh'])
            result = app.api_translate_selection(dict(user_id=self.user, selected_text='иде́я', exam_system='GENERAL'))
            self.assertEqual(result['lemma'], 'идея')
            self.assertEqual(app.clean_selection_text('лёгкий'), 'лёгкий')


if __name__ == '__main__':
    unittest.main()
