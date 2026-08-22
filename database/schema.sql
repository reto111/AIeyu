-- Russian AI Tutor initial schema
-- Target for V0.1: SQLite-compatible, with a path to PostgreSQL later.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS exam_systems (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  name_zh TEXT NOT NULL,
  name_original TEXT,
  description TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exam_levels (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exam_system_id INTEGER NOT NULL,
  code TEXT NOT NULL,
  name_zh TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
  UNIQUE (exam_system_id, code)
);

CREATE TABLE IF NOT EXISTS question_types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  name_zh TEXT NOT NULL,
  description TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_points (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exam_system_id INTEGER,
  parent_id INTEGER,
  code TEXT NOT NULL,
  name_zh TEXT NOT NULL,
  name_ru TEXT,
  category TEXT NOT NULL,
  description TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
  FOREIGN KEY (parent_id) REFERENCES knowledge_points(id),
  UNIQUE (exam_system_id, code)
);

CREATE TABLE IF NOT EXISTS source_documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exam_system_id INTEGER NOT NULL,
  level_id INTEGER,
  source_year INTEGER,
  title TEXT NOT NULL,
  document_type TEXT NOT NULL CHECK (document_type IN ('questions', 'answers', 'analysis', 'full', 'syllabus', 'notes')),
  file_path TEXT NOT NULL,
  file_hash TEXT,
  text_extract_status TEXT NOT NULL DEFAULT 'pending' CHECK (text_extract_status IN ('pending', 'extracted', 'needs_ocr', 'failed')),
  review_status TEXT NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending', 'in_review', 'reviewed', 'archived')),
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
  FOREIGN KEY (level_id) REFERENCES exam_levels(id)
);

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

CREATE TABLE IF NOT EXISTS passages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_document_id INTEGER,
  title TEXT,
  body TEXT NOT NULL,
  language TEXT NOT NULL DEFAULT 'ru',
  source_page_start INTEGER,
  source_page_end INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (source_document_id) REFERENCES source_documents(id)
);

CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exam_system_id INTEGER NOT NULL,
  level_id INTEGER NOT NULL,
  question_type_id INTEGER NOT NULL,
  passage_id INTEGER,
  source_document_id INTEGER,
  source_year INTEGER,
  source_question_number TEXT,
  stem TEXT NOT NULL,
  correct_answer TEXT,
  explanation_zh TEXT,
  difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 5),
  review_status TEXT NOT NULL DEFAULT 'draft' CHECK (review_status IN ('draft', 'needs_review', 'approved', 'rejected', 'archived')),
  generation_status TEXT NOT NULL DEFAULT 'human_imported' CHECK (generation_status IN ('human_imported', 'ai_draft', 'ai_review_pending', 'ai_approved', 'practice_only')),
  source_page INTEGER,
  raw_text TEXT,
  source_usage TEXT NOT NULL DEFAULT 'practice' CHECK (source_usage IN ('source_reference_only', 'practice')),
  content_origin TEXT NOT NULL DEFAULT 'past_exam_original' CHECK (content_origin IN ('past_exam_original', 'ai_rewritten', 'ai_generated', 'manual')),
  source_label TEXT,
  requires_source_label INTEGER NOT NULL DEFAULT 1 CHECK (requires_source_label IN (0, 1)),
  rewrite_source_question_id INTEGER,
  similarity_review_status TEXT NOT NULL DEFAULT 'not_checked' CHECK (similarity_review_status IN ('not_checked', 'passed', 'flagged', 'failed')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
  FOREIGN KEY (level_id) REFERENCES exam_levels(id),
  FOREIGN KEY (question_type_id) REFERENCES question_types(id),
  FOREIGN KEY (passage_id) REFERENCES passages(id),
  FOREIGN KEY (source_document_id) REFERENCES source_documents(id),
  FOREIGN KEY (rewrite_source_question_id) REFERENCES questions(id)
);

CREATE TABLE IF NOT EXISTS question_options (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER NOT NULL,
  option_key TEXT NOT NULL,
  option_text TEXT NOT NULL,
  explanation_zh TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
  UNIQUE (question_id, option_key)
);

CREATE TABLE IF NOT EXISTS question_knowledge_points (
  question_id INTEGER NOT NULL,
  knowledge_point_id INTEGER NOT NULL,
  weight REAL NOT NULL DEFAULT 1.0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (question_id, knowledge_point_id),
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
  FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_points(id)
);

CREATE TABLE IF NOT EXISTS question_generation_references (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER NOT NULL,
  knowledge_chunk_id INTEGER NOT NULL,
  role TEXT NOT NULL DEFAULT 'source_context' CHECK (role IN ('source_context', 'style_reference', 'similarity_reference')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
  FOREIGN KEY (knowledge_chunk_id) REFERENCES knowledge_chunks(id),
  UNIQUE (question_id, knowledge_chunk_id, role)
);

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

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  display_name TEXT NOT NULL,
  email TEXT UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_auth (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  login_name TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  token_hash TEXT NOT NULL UNIQUE,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS quiz_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  exam_system_id INTEGER NOT NULL,
  level_id INTEGER NOT NULL,
  title TEXT,
  mode TEXT NOT NULL DEFAULT 'random' CHECK (mode IN ('random', 'knowledge_point', 'weakness_review', 'mock_exam')),
  status TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'submitted', 'reviewed', 'abandoned')),
  total_questions INTEGER NOT NULL DEFAULT 0,
  correct_count INTEGER NOT NULL DEFAULT 0,
  accuracy REAL,
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  submitted_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
  FOREIGN KEY (level_id) REFERENCES exam_levels(id)
);

CREATE TABLE IF NOT EXISTS quiz_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  quiz_session_id INTEGER NOT NULL,
  question_id INTEGER NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (quiz_session_id) REFERENCES quiz_sessions(id) ON DELETE CASCADE,
  FOREIGN KEY (question_id) REFERENCES questions(id)
);

CREATE TABLE IF NOT EXISTS user_answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  quiz_item_id INTEGER NOT NULL,
  user_id INTEGER,
  selected_answer TEXT,
  is_correct INTEGER,
  answered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (quiz_item_id) REFERENCES quiz_items(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS question_exposures (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  question_id INTEGER NOT NULL,
  first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  seen_count INTEGER NOT NULL DEFAULT 0,
  correct_count INTEGER NOT NULL DEFAULT 0,
  wrong_count INTEGER NOT NULL DEFAULT 0,
  last_is_correct INTEGER CHECK (last_is_correct IN (0, 1)),
  last_quiz_session_id INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (question_id) REFERENCES questions(id),
  FOREIGN KEY (last_quiz_session_id) REFERENCES quiz_sessions(id),
  UNIQUE (user_id, question_id)
);

CREATE TABLE IF NOT EXISTS weakness_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  quiz_session_id INTEGER,
  knowledge_point_id INTEGER NOT NULL,
  attempted_count INTEGER NOT NULL DEFAULT 0,
  wrong_count INTEGER NOT NULL DEFAULT 0,
  accuracy REAL,
  ai_summary_zh TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (quiz_session_id) REFERENCES quiz_sessions(id),
  FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_points(id)
);

CREATE TABLE IF NOT EXISTS mastery_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  exam_system_id INTEGER NOT NULL,
  level_id INTEGER NOT NULL,
  target_type TEXT NOT NULL CHECK (target_type IN ('question_type', 'knowledge_point')),
  target_code TEXT NOT NULL,
  target_name_zh TEXT,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  wrong_count INTEGER NOT NULL DEFAULT 0,
  weighted_accuracy REAL,
  mastery_score INTEGER,
  mastery_status TEXT NOT NULL CHECK (mastery_status IN ('weak', 'unstable', 'stable', 'strong', 'insufficient_data')),
  recent_wrong_streak INTEGER NOT NULL DEFAULT 0,
  weakness_priority INTEGER NOT NULL DEFAULT 0,
  last_wrong_at TEXT,
  calculated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
  FOREIGN KEY (level_id) REFERENCES exam_levels(id)
);

CREATE TABLE IF NOT EXISTS training_recommendations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  exam_system_id INTEGER NOT NULL,
  level_id INTEGER NOT NULL,
  target_type TEXT NOT NULL CHECK (target_type IN ('question_type', 'knowledge_point')),
  target_code TEXT NOT NULL,
  target_name_zh TEXT,
  reason_code TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 0,
  recommended_count INTEGER NOT NULL DEFAULT 10,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'used', 'dismissed')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (exam_system_id) REFERENCES exam_systems(id),
  FOREIGN KEY (level_id) REFERENCES exam_levels(id)
);

CREATE TABLE IF NOT EXISTS ai_tutor_threads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  quiz_session_id INTEGER,
  question_id INTEGER,
  title TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (quiz_session_id) REFERENCES quiz_sessions(id),
  FOREIGN KEY (question_id) REFERENCES questions(id)
);

CREATE TABLE IF NOT EXISTS ai_tutor_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_id INTEGER NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  rag_references_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (thread_id) REFERENCES ai_tutor_threads(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target_type TEXT NOT NULL CHECK (target_type IN ('question', 'source_document', 'ai_generated_question')),
  target_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_questions_exam_level_type
  ON questions (exam_system_id, level_id, question_type_id, review_status);

CREATE INDEX IF NOT EXISTS idx_questions_source
  ON questions (source_year, source_question_number);

CREATE INDEX IF NOT EXISTS idx_questions_source_usage
  ON questions (source_usage, content_origin, generation_status, review_status, similarity_review_status);

CREATE INDEX IF NOT EXISTS idx_knowledge_sources_exam
  ON knowledge_sources (exam_system_id, level_id, source_type, review_status);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_lookup
  ON knowledge_chunks (exam_system_id, level_id, question_type_code, knowledge_point_code, review_status);

CREATE INDEX IF NOT EXISTS idx_qkp_knowledge_point
  ON question_knowledge_points (knowledge_point_id);

CREATE INDEX IF NOT EXISTS idx_question_generation_references_question
  ON question_generation_references (question_id, role);

CREATE INDEX IF NOT EXISTS idx_quiz_sessions_user
  ON quiz_sessions (user_id, started_at);

CREATE INDEX IF NOT EXISTS idx_user_answers_quiz_item
  ON user_answers (quiz_item_id);

CREATE INDEX IF NOT EXISTS idx_question_exposures_user_question
  ON question_exposures (user_id, question_id);

CREATE INDEX IF NOT EXISTS idx_mastery_snapshots_user_target
  ON mastery_snapshots (user_id, exam_system_id, level_id, target_type, target_code, calculated_at);

CREATE INDEX IF NOT EXISTS idx_training_recommendations_user_status
  ON training_recommendations (user_id, status, priority);

CREATE INDEX IF NOT EXISTS idx_user_sessions_token
  ON user_sessions (token_hash, expires_at);

INSERT OR IGNORE INTO exam_systems (code, name_zh, name_original, description)
VALUES
  ('TEM8_RU', '俄语专业八级', 'Русский язык TEM-8', '第一阶段默认考试体系'),
  ('TEM4_RU', '俄语专业四级', 'Русский язык TEM-4', '后续扩展考试体系预留，当前不导入专四资料');

INSERT OR IGNORE INTO exam_levels (exam_system_id, code, name_zh, sort_order)
SELECT id, 'TEM8', '专八', 1
FROM exam_systems
WHERE code = 'TEM8_RU';

INSERT OR IGNORE INTO exam_levels (exam_system_id, code, name_zh, sort_order)
SELECT id, 'TEM4', '专四', 1
FROM exam_systems
WHERE code = 'TEM4_RU';

INSERT OR IGNORE INTO question_types (code, name_zh, description)
VALUES
  ('grammar_choice', '语法选择题', '俄语专八语法单项选择题'),
  ('literature_choice', '文学选择题', '俄语文学相关单项选择题'),
  ('culture_choice', '国情选择题', '俄罗斯国情相关单项选择题'),
  ('reading_choice', '阅读理解选择题', '阅读文章下的单项选择题'),
  ('listening_choice', '听力理解选择题', '听力音频材料下的单项选择题');

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

