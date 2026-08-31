from __future__ import annotations

import gc
import shutil
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import serve_student_app as app  # noqa: E402


class AdaptiveTrainingTests(unittest.TestCase):
    user_id = 99001

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="aieyu_adaptive_test_"))
        self.db_path = self.temp_dir / "test.sqlite"
        shutil.copy2(ROOT / "database" / "russian_ai_tutor.sqlite", self.db_path)
        self.original_db_path = app.DB_PATH
        app.DB_PATH = self.db_path
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                "INSERT INTO users (id, display_name, email) VALUES (?, ?, ?)",
                (self.user_id, "专项训练测试", "adaptive-test@aieyu.local"),
            )
            conn.commit()

    def tearDown(self) -> None:
        app.DB_PATH = self.original_db_path
        gc.collect()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def question_id(self, exam: str, knowledge_code: str) -> int:
        with closing(sqlite3.connect(self.db_path)) as conn:
            row = conn.execute(
                """
                SELECT q.id
                FROM questions q
                JOIN exam_systems es ON es.id = q.exam_system_id
                JOIN question_knowledge_points qkp ON qkp.question_id = q.id
                JOIN knowledge_points kp ON kp.id = qkp.knowledge_point_id
                WHERE es.code = ? AND kp.code = ?
                  AND q.review_status = 'approved' AND q.source_usage = 'practice'
                ORDER BY q.id
                LIMIT 1
                """,
                (exam, knowledge_code),
            ).fetchone()
        self.assertIsNotNone(row, f"Missing test question for {exam}/{knowledge_code}")
        return int(row[0])

    def add_attempts(self, exam: str, level: str, question_id: int, answers: list[bool]) -> None:
        with closing(sqlite3.connect(self.db_path)) as conn:
            system_id = int(conn.execute("SELECT id FROM exam_systems WHERE code = ?", (exam,)).fetchone()[0])
            level_id = int(
                conn.execute(
                    "SELECT id FROM exam_levels WHERE exam_system_id = ? AND code = ?",
                    (system_id, level),
                ).fetchone()[0]
            )
            session_id = int(
                conn.execute(
                    """
                    INSERT INTO quiz_sessions (
                      user_id, exam_system_id, level_id, title, mode, status,
                      total_questions, correct_count, accuracy, submitted_at
                    )
                    VALUES (?, ?, ?, 'adaptive test', 'weakness_review', 'submitted', ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        self.user_id,
                        system_id,
                        level_id,
                        len(answers),
                        sum(answers),
                        sum(answers) / len(answers),
                    ),
                ).lastrowid
            )
            for index, is_correct in enumerate(answers, start=1):
                item_id = int(
                    conn.execute(
                        "INSERT INTO quiz_items (quiz_session_id, question_id, sort_order) VALUES (?, ?, ?)",
                        (session_id, question_id, index),
                    ).lastrowid
                )
                conn.execute(
                    """
                    INSERT INTO user_answers (quiz_item_id, user_id, selected_answer, is_correct)
                    VALUES (?, ?, 'A', ?)
                    """,
                    (item_id, self.user_id, int(is_correct)),
                )
            conn.commit()

    def test_language_weakness_is_prioritized_over_culture(self) -> None:
        grammar_id = self.question_id("TEM4_RU", "grammar.aspect")
        culture_id = self.question_id("TEM4_RU", "culture.history")
        self.add_attempts("TEM4_RU", "TEM4", grammar_id, [False] * 5)
        self.add_attempts("TEM4_RU", "TEM4", culture_id, [False] * 5)

        profile = app.api_profile(self.user_id, "TEM4_RU", "TEM4")

        self.assertEqual(profile["next_training"]["target_code"], "grammar.aspect")
        self.assertGreater(profile["next_training"]["focus_weight"], 1)

    def test_fine_shortage_falls_back_only_within_same_type(self) -> None:
        grammar_id = self.question_id("TEM4_RU", "grammar.aspect")
        self.add_attempts("TEM4_RU", "TEM4", grammar_id, [False] * 5)

        quiz = app.api_generate_quiz(
            {
                "user_id": self.user_id,
                "mode": "weakness_review",
                "exam_system": "TEM4_RU",
                "level": "TEM4",
                "count": 10,
                "seed": 20260831,
            }
        )

        self.assertEqual(quiz["training"]["target_code"], "grammar.aspect")
        self.assertTrue(quiz["training"]["fallback_used"])
        self.assertEqual({item["question_type"] for item in quiz["questions"]}, {"grammar_choice"})
        self.assertEqual(quiz["count"], 10)

    def test_reading_specialization_keeps_complete_passages(self) -> None:
        reading_id = self.question_id("TEM4_RU", "reading.main_idea")
        self.add_attempts("TEM4_RU", "TEM4", reading_id, [False] * 5)

        quiz = app.api_generate_quiz(
            {
                "user_id": self.user_id,
                "mode": "weakness_review",
                "exam_system": "TEM4_RU",
                "level": "TEM4",
                "count": 5,
                "seed": 20260831,
            }
        )

        returned_by_passage: dict[int, set[int]] = {}
        for item in quiz["questions"]:
            passage = item.get("passage")
            if passage:
                returned_by_passage.setdefault(int(passage["id"]), set()).add(int(item["question_id"]))
        self.assertTrue(returned_by_passage)
        with closing(sqlite3.connect(self.db_path)) as conn:
            for passage_id, returned_ids in returned_by_passage.items():
                full_ids = {
                    int(row[0])
                    for row in conn.execute(
                        """
                        SELECT id FROM questions
                        WHERE passage_id = ? AND review_status = 'approved' AND source_usage = 'practice'
                        """,
                        (passage_id,),
                    )
                }
                self.assertEqual(returned_ids, full_ids)

    def test_existing_random_quiz_path_still_works(self) -> None:
        quiz = app.api_generate_quiz(
            {
                "user_id": self.user_id,
                "mode": "random",
                "exam_system": "TEM4_RU",
                "level": "TEM4",
                "count": 10,
                "seed": 20260831,
            }
        )

        self.assertEqual(quiz["count"], 10)
        self.assertIsNone(quiz["training"])
        self.assertNotIn("reading_choice", {item["question_type"] for item in quiz["questions"]})

    def test_existing_diagnostic_path_still_covers_four_types(self) -> None:
        quiz = app.api_generate_quiz(
            {
                "user_id": self.user_id,
                "mode": "diagnostic",
                "exam_system": "TEM8_RU",
                "level": "TEM8",
                "count": 30,
                "seed": 20260831,
            }
        )

        self.assertGreaterEqual(quiz["count"], 30)
        self.assertEqual(
            {item["question_type"] for item in quiz["questions"]},
            {"grammar_choice", "literature_choice", "culture_choice", "reading_choice"},
        )


if __name__ == "__main__":
    unittest.main()
