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
import audit_question_bank_quality as quality_audit  # noqa: E402
import tag_question_knowledge_points as tagger  # noqa: E402


class AdaptiveTrainingTests(unittest.TestCase):
    user_id = 99001
    other_user_id = 99002

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
            conn.execute(
                "INSERT INTO users (id, display_name, email) VALUES (?, ?, ?)",
                (self.other_user_id, "隔离账号测试", "adaptive-isolation@aieyu.local"),
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
                app.record_question_exposure(
                    conn,
                    self.user_id,
                    session_id,
                    question_id,
                    is_correct,
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

        profile = app.api_profile(self.user_id, "TEM4_RU", "TEM4")
        self.assertFalse(any(item["target_code"].startswith("reading.") for item in profile["knowledge_mastery"]))
        self.assertEqual(profile["next_training"]["target_code"], "reading_choice")

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

        wrongbook_quiz = app.api_generate_quiz(
            {
                "user_id": self.user_id,
                "mode": "wrongbook_review",
                "question_ids": [reading_id],
                "exam_system": "TEM4_RU",
                "level": "TEM4",
                "count": 1,
                "seed": 20260901,
            }
        )
        passage_id = int(wrongbook_quiz["questions"][0]["passage"]["id"])
        returned_ids = {int(item["question_id"]) for item in wrongbook_quiz["questions"]}
        with closing(sqlite3.connect(self.db_path)) as conn:
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

    def test_student_can_start_an_explicit_knowledge_point(self) -> None:
        quiz = app.api_generate_quiz(
            {
                "user_id": self.user_id,
                "mode": "knowledge_point",
                "target_code": "grammar.aspect",
                "exam_system": "TEM4_RU",
                "level": "TEM4",
                "count": 10,
                "seed": 20260831,
            }
        )

        self.assertEqual(quiz["mode"], "knowledge_point")
        self.assertEqual(quiz["training"]["target_code"], "grammar.aspect")
        self.assertEqual({item["question_type"] for item in quiz["questions"]}, {"grammar_choice"})

    def test_study_center_is_isolated_by_user(self) -> None:
        grammar_id = self.question_id("TEM4_RU", "grammar.aspect")
        self.add_attempts("TEM4_RU", "TEM4", grammar_id, [True, False, True, False, True])

        current = app.api_study_center(self.user_id, "TEM4_RU", "TEM4")
        other = app.api_study_center(self.other_user_id, "TEM4_RU", "TEM4")

        self.assertEqual(current["periods"]["seven_days"]["attempted"], 5)
        self.assertEqual(other["periods"]["seven_days"]["attempted"], 0)
        self.assertEqual(len(current["daily_trend"]), 7)
        self.assertTrue(any(item["target_code"] == "grammar.aspect" for item in current["knowledge_mastery"]))
        self.assertFalse(any(item["category"] == "reading" for item in current["knowledge_mastery"]))

    def test_literature_tags_follow_learning_task_instead_of_era(self) -> None:
        author = tagger.classify_literature(
            "Знаменитый роман «Белая гвардия» написал ____.",
            ["А. Н. Толстой", "М. Горький", "М. А. Булгаков", "А. П. Чехов"],
        )
        content = tagger.classify_literature(
            "Главными героями романа «Доктор Живаго» являются ____.",
            ["Евгений и Татьяна", "Юрий и Лара", "Родион и Сонечка", "Андрей и Наташа"],
        )
        history = tagger.classify_literature(
            "Как литературное направление модернизм появился в России ____.",
            ["в XIX веке", "на рубеже XIX-XX веков"],
        )

        self.assertEqual(author.code, "literature.author_work")
        self.assertEqual(content.code, "literature.work_content")
        self.assertEqual(history.code, "literature.history_movements")

    def test_approved_practice_questions_have_no_high_or_medium_audit_issues(self) -> None:
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            questions = quality_audit.load_questions(conn)
            options = quality_audit.load_options(conn)
            issues = [
                issue
                for question in questions
                for issue in quality_audit.audit_question(question, options.get(question["id"], []))
                if question["review_status"] == "approved"
                and question["source_usage"] == "practice"
                and issue["severity"] in {"high", "medium"}
            ]

        self.assertEqual(issues, [])

    def test_wrongbook_preferences_and_review_are_isolated_by_user(self) -> None:
        question_id = self.question_id("TEM4_RU", "grammar.aspect")
        self.add_attempts("TEM4_RU", "TEM4", question_id, [False, False])

        wrongbook = app.api_wrongbook(self.user_id, 80, "TEM4_RU", "TEM4")
        item = next(entry for entry in wrongbook["items"] if entry["question_id"] == question_id)
        self.assertEqual(item["status"], "pending")
        self.assertTrue(item["is_repeat_wrong"])
        self.assertEqual(wrongbook["repeat_wrong_count"], 1)
        self.assertTrue(item["options"])
        self.assertTrue(item["knowledge_points"])

        saved = app.api_update_wrongbook_item(
            {
                "user_id": self.user_id,
                "question_id": question_id,
                "note_text": "动词体要结合上下文判断。",
                "is_favorite": True,
            }
        )
        self.assertTrue(saved["is_favorite"])
        refreshed = app.api_wrongbook(self.user_id, 80, "TEM4_RU", "TEM4")
        refreshed_item = next(entry for entry in refreshed["items"] if entry["question_id"] == question_id)
        self.assertEqual(refreshed_item["note_text"], "动词体要结合上下文判断。")
        self.assertEqual(refreshed["favorite_count"], 1)

        other = app.api_wrongbook(self.other_user_id, 80, "TEM4_RU", "TEM4")
        self.assertEqual(other["count"], 0)
        with self.assertRaisesRegex(ValueError, "不在当前账号"):
            app.api_update_wrongbook_item(
                {
                    "user_id": self.other_user_id,
                    "question_id": question_id,
                    "note_text": "不应写入",
                    "is_favorite": True,
                }
            )

        quiz = app.api_generate_quiz(
            {
                "user_id": self.user_id,
                "mode": "wrongbook_review",
                "question_ids": [question_id],
                "exam_system": "TEM4_RU",
                "level": "TEM4",
                "count": 1,
                "seed": 20260901,
            }
        )
        self.assertEqual(quiz["mode"], "wrongbook_review")
        self.assertEqual([entry["question_id"] for entry in quiz["questions"]], [question_id])
        with self.assertRaisesRegex(ValueError, "不属于当前账号"):
            app.api_generate_quiz(
                {
                    "user_id": self.other_user_id,
                    "mode": "wrongbook_review",
                    "question_ids": [question_id],
                    "exam_system": "TEM4_RU",
                    "level": "TEM4",
                    "count": 1,
                }
            )

        self.add_attempts("TEM4_RU", "TEM4", question_id, [True])
        corrected = app.api_wrongbook(self.user_id, 80, "TEM4_RU", "TEM4")
        corrected_item = next(entry for entry in corrected["items"] if entry["question_id"] == question_id)
        self.assertEqual(corrected_item["status"], "corrected")


if __name__ == "__main__":
    unittest.main()
