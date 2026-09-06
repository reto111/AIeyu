import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from content_patch import apply_patch, digest, connect, DEFAULT_MANIFEST, ROOT


class ContentPatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / 'test.sqlite'
        con = sqlite3.connect(self.db)
        con.executescript('''CREATE TABLE exam_systems(id INTEGER PRIMARY KEY,code TEXT);
            INSERT INTO exam_systems VALUES(99,'TEM8_RU');
            CREATE TABLE questions(id INTEGER PRIMARY KEY,exam_system_id INTEGER,source_year INTEGER,
                source_question_number TEXT,content_origin TEXT,passage_id INTEGER,stem TEXT,
                review_status TEXT,updated_at TEXT);
            INSERT INTO questions VALUES(500,99,2017,'16','past_exam_original',NULL,'old','approved',NULL);
            CREATE TABLE users(id INTEGER,name TEXT); INSERT INTO users VALUES(1,'server student');
            CREATE TABLE question_review_logs(id INTEGER,review_decision TEXT);
            INSERT INTO question_review_logs VALUES(1,'needs_review');''')
        con.commit()
        con.close()
        self.manifest = self.root / 'patch.json'
        self.manifest.write_text(json.dumps({'schema_version': 1, 'patch_id': 'test', 'items': [
            {'key': ['TEM8_RU',2017,'16'], 'field': 'stem', 'old_hash': digest('old'), 'new': 'new'}]}), encoding='utf-8')

    def run_patch(self, apply=False):
        return apply_patch(self.db, self.manifest, apply, self.root / 'reports')

    def value(self, sql):
        con = sqlite3.connect(self.db)
        try:
            return con.execute(sql).fetchall()
        finally:
            con.close()

    def test_preview_then_apply_and_repeat_preserves_students_and_history(self):
        self.assertEqual(self.run_patch()['changed_fields'], 1)
        self.assertEqual(self.value('SELECT stem FROM questions'), [('old',)])
        result = self.run_patch(True)
        self.assertEqual(result['status'], 'applied')
        self.assertTrue(Path(result['backup']).exists())
        self.assertEqual(self.value('SELECT stem FROM questions'), [('new',)])
        self.assertEqual(self.value('SELECT * FROM users'), [(1,'server student')])
        self.assertEqual(self.value('SELECT * FROM question_review_logs'), [(1,'needs_review')])
        self.assertEqual(self.run_patch(True)['changed_fields'], 0)
        self.assertEqual(self.value('SELECT count(*) FROM content_patch_events'), [(1,)])

    def test_manual_change_conflicts(self):
        with connect(self.db, writable=True) as con:
            con.execute("UPDATE questions SET stem='later correction'")
        self.assertEqual(self.run_patch(True)['status'], 'conflict')
        self.assertEqual(self.value('SELECT stem FROM questions'), [('later correction',)])

    def test_missing_key_blocks_all_fields(self):
        data = json.loads(self.manifest.read_text())
        data['items'].append({'key':['TEM8_RU',2017,'999'], 'field':'stem', 'old_hash':digest('x'), 'new':'y'})
        self.manifest.write_text(json.dumps(data))
        self.assertEqual(self.run_patch(True)['status'], 'conflict')
        self.assertEqual(self.value('SELECT stem FROM questions'), [('old',)])

    def test_missing_database_does_not_create_empty_file(self):
        missing = self.root / 'missing.sqlite'
        with self.assertRaises(sqlite3.OperationalError):
            apply_patch(missing, self.manifest)
        self.assertFalse(missing.exists())

    def test_real_historical_snapshot_preserves_all_non_content_tables(self):
        baseline = ROOT / 'data/processed/backups/russian_ai_tutor_before_multimodal_fixes_20260903_191321.sqlite'
        if not baseline.exists():
            self.skipTest('Historical local snapshot unavailable; synthetic tests remain portable')
        copy = self.root / 'historical.sqlite'
        with connect(baseline) as src, closing(sqlite3.connect(copy)) as dst:
            src.backup(dst)
        def snapshot():
            with connect(copy) as con:
                names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
                         if r[0] not in ('questions','question_options','passages','sqlite_sequence','content_patch_events')]
                result = {name: sorted(repr(tuple(row)) for row in con.execute('SELECT * FROM "' + name.replace('"','""') + '"'))
                          for name in names}
                for name, allowed in [('questions', {'stem','correct_answer','source_page','updated_at'}),
                                      ('question_options', {'option_text','updated_at'}),
                                      ('passages', {'body','updated_at'})]:
                    columns = [r[1] for r in con.execute(f'PRAGMA table_info({name})') if r[1] not in allowed]
                    result[name] = sorted(repr(tuple(r)) for r in con.execute(f'SELECT {",".join(columns)} FROM {name}'))
                return result
        before = snapshot()
        result = apply_patch(copy, DEFAULT_MANIFEST, True, self.root / 'real_reports')
        self.assertEqual(result['conflicts'], [])
        self.assertEqual(result['changed_fields'], 139)
        self.assertEqual(snapshot(), before)
        self.assertEqual(apply_patch(copy, DEFAULT_MANIFEST, True, self.root / 'real_reports')['changed_fields'], 0)

    def test_duplicate_source_key_blocks_write(self):
        with connect(self.db, writable=True) as con:
            con.execute("INSERT INTO questions SELECT 501,exam_system_id,source_year,source_question_number,content_origin,passage_id,stem,review_status,updated_at FROM questions WHERE id=500")
        self.assertEqual(self.run_patch(True)['status'], 'conflict')
        self.assertEqual(self.value('SELECT stem FROM questions'), [('old',), ('old',)])


if __name__ == '__main__':
    unittest.main()
