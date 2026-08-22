from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
WORD_PDF = ROOT / "data" / "words" / "tem8_russian_words.pdf"
MANIFEST_PATH = ROOT / "data" / "processed" / "words" / "ocr_text" / "tem8_russian_words_ocr_manifest.json"


DDL = """
CREATE TABLE IF NOT EXISTS word_sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exam_system_id INTEGER NOT NULL,
  level_id INTEGER,
  title TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_hash TEXT,
  file_size_bytes INTEGER,
  page_count INTEGER,
  source_type TEXT NOT NULL DEFAULT 'word_list' CHECK (source_type IN ('word_list', 'textbook', 'manual', 'ocr_extract')),
  ocr_status TEXT NOT NULL DEFAULT 'pending' CHECK (ocr_status IN ('pending', 'needs_ocr', 'ocr_done', 'failed', 'skipped')),
  review_status TEXT NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending', 'in_review', 'reviewed', 'archived')),
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
  FOREIGN KEY (level_id) REFERENCES exam_levels(id),
  UNIQUE (exam_system_id, file_path)
);

CREATE TABLE IF NOT EXISTS vocabulary_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exam_system_id INTEGER NOT NULL,
  level_id INTEGER,
  word TEXT NOT NULL,
  lemma TEXT,
  accent TEXT,
  part_of_speech TEXT,
  meaning_zh TEXT NOT NULL,
  meaning_en TEXT,
  difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 5),
  frequency_rank INTEGER,
  source_id INTEGER,
  source_page INTEGER,
  source_line TEXT,
  raw_text TEXT,
  review_status TEXT NOT NULL DEFAULT 'needs_review' CHECK (review_status IN ('draft', 'needs_review', 'approved', 'rejected', 'archived')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
  FOREIGN KEY (level_id) REFERENCES exam_levels(id),
  FOREIGN KEY (source_id) REFERENCES word_sources(id),
  UNIQUE (exam_system_id, level_id, word, part_of_speech)
);

CREATE TABLE IF NOT EXISTS vocabulary_forms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vocabulary_item_id INTEGER NOT NULL,
  form_text TEXT NOT NULL,
  form_type TEXT NOT NULL CHECK (form_type IN ('inflected_form', 'same_root', 'derived_word', 'collocation', 'synonym', 'antonym', 'example')),
  meaning_zh TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (vocabulary_item_id) REFERENCES vocabulary_items(id) ON DELETE CASCADE,
  UNIQUE (vocabulary_item_id, form_text, form_type)
);

CREATE TABLE IF NOT EXISTS user_word_progress (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  vocabulary_item_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'learning', 'fuzzy', 'known', 'mastered')),
  seen_count INTEGER NOT NULL DEFAULT 0,
  correct_count INTEGER NOT NULL DEFAULT 0,
  wrong_count INTEGER NOT NULL DEFAULT 0,
  last_seen_at TEXT,
  next_review_at TEXT,
  ease_factor REAL NOT NULL DEFAULT 2.5,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (vocabulary_item_id) REFERENCES vocabulary_items(id) ON DELETE CASCADE,
  UNIQUE (user_id, vocabulary_item_id)
);

CREATE TABLE IF NOT EXISTS word_review_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  vocabulary_item_id INTEGER NOT NULL,
  review_mode TEXT NOT NULL DEFAULT 'daily_checkin' CHECK (review_mode IN ('daily_checkin', 'weak_review', 'random_review')),
  prompt_type TEXT NOT NULL DEFAULT 'ru_to_zh' CHECK (prompt_type IN ('ru_to_zh', 'zh_to_ru', 'choice', 'spelling')),
  user_response TEXT,
  result TEXT NOT NULL CHECK (result IN ('unknown', 'fuzzy', 'known', 'mastered', 'wrong', 'correct')),
  reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (vocabulary_item_id) REFERENCES vocabulary_items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_vocabulary_items_lookup
  ON vocabulary_items (exam_system_id, level_id, review_status, word);

CREATE INDEX IF NOT EXISTS idx_user_word_progress_due
  ON user_word_progress (user_id, status, next_review_at);

CREATE INDEX IF NOT EXISTS idx_word_review_logs_user_time
  ON word_review_logs (user_id, reviewed_at);
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_tem8_ids(conn: sqlite3.Connection) -> tuple[int, int]:
    exam_system_id = int(conn.execute("SELECT id FROM exam_systems WHERE code = 'TEM8_RU'").fetchone()[0])
    level_id = int(
        conn.execute(
            "SELECT id FROM exam_levels WHERE exam_system_id = ? AND code = 'TEM8'",
            (exam_system_id,),
        ).fetchone()[0]
    )
    return exam_system_id, level_id


def register_word_source(conn: sqlite3.Connection) -> int | None:
    if not WORD_PDF.exists():
        return None
    exam_system_id, level_id = fetch_tem8_ids(conn)
    page_count = None
    manifest_notes = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        page_count = int(manifest.get("page_count") or 0) or None
        manifest_notes = {
            "ocr_combined_path": manifest.get("combined_path"),
            "ocr_lang": manifest.get("lang"),
            "ocr_dpi": manifest.get("dpi"),
        }
    conn.execute(
        """
        INSERT INTO word_sources (
          exam_system_id, level_id, title, file_path, file_name, file_hash,
          file_size_bytes, page_count, source_type, ocr_status, review_status, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'word_list', 'ocr_done', 'in_review', ?)
        ON CONFLICT(exam_system_id, file_path) DO UPDATE SET
          file_hash = excluded.file_hash,
          file_size_bytes = excluded.file_size_bytes,
          page_count = excluded.page_count,
          ocr_status = excluded.ocr_status,
          review_status = excluded.review_status,
          notes = excluded.notes,
          updated_at = CURRENT_TIMESTAMP
        """,
        (
            exam_system_id,
            level_id,
            "俄语专八词汇 OCR 词库",
            str(WORD_PDF.relative_to(ROOT)).replace("\\", "/"),
            WORD_PDF.name,
            sha256(WORD_PDF),
            WORD_PDF.stat().st_size,
            page_count,
            json.dumps(manifest_notes, ensure_ascii=False),
        ),
    )
    row = conn.execute(
        "SELECT id FROM word_sources WHERE exam_system_id = ? AND file_path = ?",
        (exam_system_id, str(WORD_PDF.relative_to(ROOT)).replace("\\", "/")),
    ).fetchone()
    return int(row[0]) if row else None


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(DDL)
        source_id = register_word_source(conn)
        conn.commit()
        counts = {
            "word_sources": conn.execute("SELECT COUNT(*) FROM word_sources").fetchone()[0],
            "vocabulary_items": conn.execute("SELECT COUNT(*) FROM vocabulary_items").fetchone()[0],
            "user_word_progress": conn.execute("SELECT COUNT(*) FROM user_word_progress").fetchone()[0],
        }
    print(json.dumps({"status": "ok", "source_id": source_id, **counts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
