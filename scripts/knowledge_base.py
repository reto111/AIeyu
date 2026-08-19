from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_knowledge_base_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS knowledge_sources (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          exam_system_id INTEGER NOT NULL,
          level_id INTEGER,
          title TEXT NOT NULL,
          source_type TEXT NOT NULL CHECK (source_type IN ('syllabus', 'grammar_note', 'literature_note', 'culture_note', 'reading_note', 'manual_note', 'reference_book', 'web_article')),
          file_path TEXT NOT NULL,
          file_hash TEXT,
          language TEXT NOT NULL DEFAULT 'zh',
          trust_level INTEGER NOT NULL DEFAULT 2 CHECK (trust_level BETWEEN 1 AND 5),
          review_status TEXT NOT NULL DEFAULT 'draft' CHECK (review_status IN ('draft', 'reviewed', 'archived')),
          notes TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
          FOREIGN KEY (level_id) REFERENCES exam_levels(id),
          UNIQUE (exam_system_id, file_path)
        );

        CREATE TABLE IF NOT EXISTS knowledge_chunks (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source_id INTEGER NOT NULL,
          exam_system_id INTEGER NOT NULL,
          level_id INTEGER,
          chunk_code TEXT,
          title TEXT NOT NULL,
          body TEXT NOT NULL,
          language TEXT NOT NULL DEFAULT 'zh',
          question_type_code TEXT,
          knowledge_point_code TEXT,
          tags_json TEXT,
          source_locator TEXT,
          token_count INTEGER NOT NULL DEFAULT 0,
          embedding_status TEXT NOT NULL DEFAULT 'not_indexed' CHECK (embedding_status IN ('not_indexed', 'indexed', 'failed')),
          review_status TEXT NOT NULL DEFAULT 'draft' CHECK (review_status IN ('draft', 'reviewed', 'archived')),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (source_id) REFERENCES knowledge_sources(id) ON DELETE CASCADE,
          FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
          FOREIGN KEY (level_id) REFERENCES exam_levels(id)
        );

        CREATE INDEX IF NOT EXISTS idx_knowledge_sources_exam
          ON knowledge_sources (exam_system_id, level_id, source_type, review_status);

        CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_lookup
          ON knowledge_chunks (exam_system_id, level_id, question_type_code, knowledge_point_code, review_status);
        """
    )


def fetch_tem8_ids(conn: sqlite3.Connection) -> tuple[int, int]:
    exam_system = conn.execute("SELECT id FROM exam_systems WHERE code = 'TEM8_RU'").fetchone()
    if exam_system is None:
        raise ValueError("Missing exam system TEM8_RU. Initialize the database first.")
    level = conn.execute(
        "SELECT id FROM exam_levels WHERE exam_system_id = ? AND code = 'TEM8'",
        (int(exam_system["id"]),),
    ).fetchone()
    if level is None:
        raise ValueError("Missing exam level TEM8. Initialize the database first.")
    return int(exam_system["id"]), int(level["id"])


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative_to_root(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()
