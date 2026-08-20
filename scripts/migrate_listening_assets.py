from __future__ import annotations

import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"


DDL = """
CREATE TABLE IF NOT EXISTS listening_assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exam_system_id INTEGER NOT NULL,
  level_id INTEGER,
  source_year INTEGER,
  title TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_hash TEXT,
  file_format TEXT,
  file_size_bytes INTEGER,
  duration_seconds REAL,
  asset_scope TEXT NOT NULL DEFAULT 'segment' CHECK (asset_scope IN ('full_exam', 'section', 'segment')),
  segment_order INTEGER,
  segment_label TEXT,
  language TEXT NOT NULL DEFAULT 'ru',
  source_label TEXT,
  asr_status TEXT NOT NULL DEFAULT 'pending' CHECK (asr_status IN ('pending', 'asr_draft', 'human_verified', 'failed', 'skipped')),
  transcript_status TEXT NOT NULL DEFAULT 'no_transcript' CHECK (transcript_status IN ('no_transcript', 'asr_draft', 'human_verified')),
  review_status TEXT NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending', 'in_review', 'reviewed', 'archived')),
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
  FOREIGN KEY (level_id) REFERENCES exam_levels(id),
  UNIQUE (exam_system_id, file_path)
);

CREATE TABLE IF NOT EXISTS listening_transcripts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  audio_asset_id INTEGER NOT NULL,
  transcript_type TEXT NOT NULL CHECK (transcript_type IN ('asr_raw', 'human_corrected')),
  provider TEXT,
  model_name TEXT,
  language TEXT NOT NULL DEFAULT 'ru',
  transcript_text TEXT NOT NULL,
  confidence REAL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (audio_asset_id) REFERENCES listening_assets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS listening_segments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  audio_asset_id INTEGER NOT NULL,
  segment_order INTEGER NOT NULL DEFAULT 0,
  start_seconds REAL,
  end_seconds REAL,
  text_ru TEXT,
  text_zh TEXT,
  review_status TEXT NOT NULL DEFAULT 'draft' CHECK (review_status IN ('draft', 'reviewed', 'archived')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (audio_asset_id) REFERENCES listening_assets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS listening_question_links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER NOT NULL,
  audio_asset_id INTEGER NOT NULL,
  listening_segment_id INTEGER,
  relation TEXT NOT NULL DEFAULT 'source_audio' CHECK (relation IN ('source_audio', 'evidence_segment', 'whole_group')),
  start_seconds REAL,
  end_seconds REAL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
  FOREIGN KEY (audio_asset_id) REFERENCES listening_assets(id),
  FOREIGN KEY (listening_segment_id) REFERENCES listening_segments(id),
  UNIQUE (question_id, audio_asset_id, listening_segment_id, relation)
);

CREATE INDEX IF NOT EXISTS idx_listening_assets_year
  ON listening_assets (exam_system_id, level_id, source_year, asset_scope, segment_order);

CREATE INDEX IF NOT EXISTS idx_listening_question_links_question
  ON listening_question_links (question_id);
"""


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(DDL)
        conn.execute(
            """
            INSERT OR IGNORE INTO question_types (code, name_zh, description)
            VALUES ('listening_choice', '听力理解选择题', '听力音频材料下的单项选择题')
            """
        )
        conn.commit()

        assets = conn.execute("SELECT COUNT(*) FROM listening_assets").fetchone()[0]
        transcripts = conn.execute("SELECT COUNT(*) FROM listening_transcripts").fetchone()[0]
        segments = conn.execute("SELECT COUNT(*) FROM listening_segments").fetchone()[0]

    print(
        json.dumps(
            {
                "status": "ok",
                "listening_assets": assets,
                "listening_transcripts": transcripts,
                "listening_segments": segments,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
