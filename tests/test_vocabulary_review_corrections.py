import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import correct_vocabulary_noak_meaning as noak
import correct_learning_umytsya_note as note
import import_vocabulary_learning as importer


class ReviewCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = self.root / 'copy.sqlite'
        with closing(sqlite3.connect(ROOT / 'database/russian_ai_tutor.sqlite')) as source:
            with closing(sqlite3.connect(self.db)) as target:
                source.backup(target)

    def tearDown(self):
        self.temp.cleanup()

    def test_noak_guard_backup_idempotence_and_history(self):
        with closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute('DELETE FROM vocabulary_learning_annotations WHERE vocabulary_item_id=6229')
            conn.execute('UPDATE vocabulary_items SET meaning_zh=? WHERE id=6229', (noak.OLD,))
            before = conn.execute('SELECT * FROM user_word_progress').fetchall()
        self.assertEqual(noak.correct(self.db)['state'], 'pending')
        result = noak.correct(self.db, True, self.root / 'backups')
        self.assertTrue(result['database_written'])
        with closing(sqlite3.connect(result['backup'])) as conn:
            self.assertEqual(conn.execute('SELECT meaning_zh FROM vocabulary_items WHERE id=6229').fetchone()[0], noak.OLD)
        self.assertFalse(noak.correct(self.db, True, self.root / 'backups')['database_written'])
        with closing(sqlite3.connect(self.db)) as conn, conn:
            self.assertEqual(conn.execute('SELECT meaning_zh FROM vocabulary_items WHERE id=6229').fetchone()[0], noak.NEW)
            self.assertEqual(conn.execute('SELECT * FROM user_word_progress').fetchall(), before)
            self.assertEqual(conn.execute('SELECT count(*) FROM vocabulary_learning_annotations WHERE vocabulary_item_id=6229').fetchone()[0], 0)
            conn.execute("UPDATE vocabulary_items SET meaning_zh='later human edit' WHERE id=6229")
        with self.assertRaisesRegex(ValueError, 'Meaning changed'):
            noak.correct(self.db, True, self.root / 'backups')

    def test_note_correction_does_not_replace_later_review(self):
        catalog = json.loads((ROOT / 'data/review_samples/learning_batch_144_catalog.json').read_text(encoding='utf-8'))
        item = next(r for r in catalog['records'] if r['id'] == 10636)
        patch = self.root / 'one.json'
        patch.write_text(json.dumps(dict(schema_version=1, records=[item]), ensure_ascii=False), encoding='utf-8')
        with closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute('DELETE FROM vocabulary_learning_annotations WHERE vocabulary_item_id=10636')
        importer.apply_catalog(self.db, patch, True, self.root / 'backups')
        self.assertEqual(note.correct(self.db)['state'], 'pending')
        self.assertTrue(note.correct(self.db, True, self.root / 'backups')['database_written'])
        self.assertFalse(note.correct(self.db, True, self.root / 'backups')['database_written'])
        with closing(sqlite3.connect(self.db)) as conn, conn:
            value = conn.execute('SELECT note FROM vocabulary_learning_annotations WHERE vocabulary_item_id=10636').fetchone()[0]
            self.assertIn('умыва́ться', value)
            self.assertNotIn('c', value)
            conn.execute("UPDATE vocabulary_learning_annotations SET note='later human edit' WHERE vocabulary_item_id=10636")
        with self.assertRaisesRegex(ValueError, 'Annotation changed'):
            note.correct(self.db, True, self.root / 'backups')


if __name__ == '__main__':
    unittest.main()
