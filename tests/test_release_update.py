import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import update_release as release
import import_vocabulary_learning as importer


class ReleaseTests(unittest.TestCase):
    def test_import_repeat_and_conflict_preserve_data(self):
        catalog = ROOT / 'dist/vocabulary_release_catalog.json'
        if not catalog.exists():
            self.skipTest('Build the release catalog first')
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / 'test.sqlite'
            with closing(sqlite3.connect(ROOT / 'database/russian_ai_tutor.sqlite')) as source:
                with closing(sqlite3.connect(db)) as target:
                    source.backup(target)
            with closing(sqlite3.connect(db)) as conn, conn:
                conn.execute('DELETE FROM vocabulary_learning_annotations')
            before = release.snapshot(db)
            expected = len(json.loads(catalog.read_text(encoding='utf-8'))['records'])
            self.assertEqual(release.update(db, catalog)['new_annotations'], expected)
            with closing(sqlite3.connect(db)) as conn:
                self.assertEqual(conn.execute('SELECT COUNT(*) FROM vocabulary_learning_annotations').fetchone()[0], 0)
            original = importer.apply_catalog
            def apply(db_path, patch_path, apply=False, backup_dir=None):
                return original(db_path, patch_path, apply, backup_dir or Path(folder) / 'backups')
            with patch.object(release, 'apply_catalog', side_effect=apply):
                self.assertEqual(release.update(db, catalog, True)['inserted'], expected)
            self.assertEqual(before, release.snapshot(db))
            self.assertEqual(release.update(db, catalog)['new_annotations'], 0)
            with closing(sqlite3.connect(db)) as conn, conn:
                conn.execute("UPDATE vocabulary_learning_annotations SET note='later manual edit' WHERE vocabulary_item_id=(SELECT MIN(vocabulary_item_id) FROM vocabulary_learning_annotations)")
            with self.assertRaises(ValueError):
                release.update(db, catalog)
            with closing(sqlite3.connect(db)) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM vocabulary_learning_annotations WHERE note='later manual edit'").fetchone()[0], 1)


if __name__ == '__main__':
    unittest.main()
