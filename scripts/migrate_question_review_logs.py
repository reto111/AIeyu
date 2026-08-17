from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"


DDL = """
CREATE TABLE IF NOT EXISTS question_review_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER NOT NULL,
  review_decision TEXT NOT NULL CHECK (review_decision IN ('approved', 'needs_review', 'needs_fix', 'rejected')),
  review_notes TEXT,
  knowledge_point_codes TEXT,
  reviewer TEXT NOT NULL DEFAULT 'manual_review',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);
"""


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(DDL)
        conn.commit()
    print(f"Ensured question_review_logs table in {DB_PATH}")


if __name__ == "__main__":
    main()
