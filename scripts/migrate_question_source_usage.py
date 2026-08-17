from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("database/russian_ai_tutor.sqlite")


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        if not column_exists(conn, "questions", "source_usage"):
            conn.execute(
                """
                ALTER TABLE questions
                ADD COLUMN source_usage TEXT NOT NULL DEFAULT 'practice'
                CHECK (source_usage IN ('source_reference_only', 'practice'))
                """
            )

        if not column_exists(conn, "questions", "content_origin"):
            conn.execute(
                """
                ALTER TABLE questions
                ADD COLUMN content_origin TEXT NOT NULL DEFAULT 'past_exam_original'
                CHECK (content_origin IN ('past_exam_original', 'ai_rewritten', 'ai_generated', 'manual'))
                """
            )

        if not column_exists(conn, "questions", "source_label"):
            conn.execute("ALTER TABLE questions ADD COLUMN source_label TEXT")

        if not column_exists(conn, "questions", "requires_source_label"):
            conn.execute(
                """
                ALTER TABLE questions
                ADD COLUMN requires_source_label INTEGER NOT NULL DEFAULT 1
                CHECK (requires_source_label IN (0, 1))
                """
            )

        if not column_exists(conn, "questions", "rewrite_source_question_id"):
            conn.execute("ALTER TABLE questions ADD COLUMN rewrite_source_question_id INTEGER")

        if not column_exists(conn, "questions", "similarity_review_status"):
            conn.execute(
                """
                ALTER TABLE questions
                ADD COLUMN similarity_review_status TEXT NOT NULL DEFAULT 'not_checked'
                CHECK (similarity_review_status IN ('not_checked', 'passed', 'flagged', 'failed'))
                """
            )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_questions_source_usage
            ON questions (source_usage, content_origin, generation_status, review_status, similarity_review_status)
            """
        )
        conn.commit()

    print("Question source usage migration complete.")


if __name__ == "__main__":
    main()
