"""Reviewed learning annotations and a shared, graded vocabulary pool."""
import json
import math


STAGE_NAMES = {1: '入门', 2: '基础', 3: '进阶', 4: '提高'}


def ensure_learning_tables(conn):
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS user_vocabulary_settings (
          user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
          student_year INTEGER CHECK(student_year BETWEEN 1 AND 4),
          starting_stage INTEGER NOT NULL DEFAULT 1 CHECK(starting_stage BETWEEN 1 AND 4),
          unlocked_stage INTEGER NOT NULL DEFAULT 1 CHECK(unlocked_stage BETWEEN 1 AND 4)
        );
        CREATE TABLE IF NOT EXISTS vocabulary_learning_annotations (
          vocabulary_item_id INTEGER PRIMARY KEY REFERENCES vocabulary_items(id) ON DELETE CASCADE,
          canonical_word TEXT NOT NULL,
          accent TEXT NOT NULL,
          part TEXT NOT NULL,
          core_meaning_zh TEXT NOT NULL,
          aspect_partner TEXT NOT NULL DEFAULT '',
          note TEXT NOT NULL DEFAULT '',
          stage INTEGER NOT NULL CHECK(stage BETWEEN 1 AND 4),
          original_json TEXT NOT NULL,
          review_method TEXT NOT NULL,
          evidence_json TEXT NOT NULL DEFAULT '[]',
          reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    columns = {row[1] for row in conn.execute('PRAGMA table_info(user_vocabulary_settings)')}
    if 'unlocked_stage' not in columns:
        conn.execute('ALTER TABLE user_vocabulary_settings ADD COLUMN unlocked_stage INTEGER NOT NULL DEFAULT 1 CHECK(unlocked_stage BETWEEN 1 AND 4)')


def parse_stage(value):
    if isinstance(value, bool) or str(value) not in ('1', '2', '3', '4'):
        raise ValueError('请选择 1 至 4 的学习阶段或年级。')
    return int(value)


def annotation(conn, row):
    item = conn.execute('SELECT * FROM vocabulary_learning_annotations WHERE vocabulary_item_id=?',
                        (row['id'],)).fetchone()
    if not item:
        return None
    original = json.loads(item['original_json'])
    # Do not hide later manual changes behind an older reviewed annotation.
    if any(row[key] != original[key] for key in ('word', 'part_of_speech', 'meaning_zh')):
        return None
    return dict(item)


def general_rows(conn, user_id):
    rows = conn.execute('''
        SELECT vi.*, a.canonical_word, a.stage,
          p.status AS progress_status, p.seen_count, p.correct_count, p.wrong_count,
          p.next_review_at, p.last_seen_at,
          EXISTS(SELECT 1 FROM word_review_logs l WHERE l.user_id=?
            AND l.vocabulary_item_id=vi.id
            AND date(l.reviewed_at)=date('now','localtime')) AS reviewed_today,
          (p.next_review_at IS NOT NULL AND
            datetime(p.next_review_at)<=datetime('now','localtime')) AS is_due,
          a.original_json
        FROM vocabulary_items vi
        JOIN vocabulary_learning_annotations a ON a.vocabulary_item_id=vi.id
        JOIN exam_systems e ON e.id=vi.exam_system_id
        LEFT JOIN user_word_progress p ON p.vocabulary_item_id=vi.id AND p.user_id=?
        WHERE vi.review_status='approved' AND e.code IN ('TEM4_RU','TEM8_RU')
        ORDER BY vi.id
    ''', (user_id, user_id)).fetchall()
    valid = []
    for row in rows:
        original = json.loads(row['original_json'])
        if all(row[key] == original[key] for key in ('word', 'part_of_speech', 'meaning_zh')):
            valid.append(row)
    # Only annotated entries are eligible. Same-spelling records are not silently
    # merged: they can be different senses and retain their existing progress IDs.
    return valid


def learning_profile(conn, user_id, rows=None):
    setting = conn.execute('SELECT * FROM user_vocabulary_settings WHERE user_id=?', (user_id,)).fetchone()
    start = setting['starting_stage'] if setting else 1
    year = setting['student_year'] if setting else None
    rows = general_rows(conn, user_id) if rows is None else rows
    stages = []
    for stage in range(1, 5):
        items = [r for r in rows if r['stage'] == stage]
        known = sum(r['progress_status'] == 'known' for r in items)
        stages.append(dict(stage=stage, name=STAGE_NAMES[stage], total=len(items), known=known))
    previous_unlocked = setting['unlocked_stage'] if setting else 1
    current = max(start, previous_unlocked)
    while current < 4:
        stats = stages[current - 1]
        if stats['total'] < 20 or stats['known'] < math.ceil(stats['total'] * .8):
            break
        if not stages[current]['total']:
            break
        current += 1
    if current > previous_unlocked:
        conn.execute('''INSERT INTO user_vocabulary_settings(user_id, student_year, starting_stage, unlocked_stage)
            VALUES (?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET unlocked_stage=excluded.unlocked_stage''',
            (user_id, year, start, current))
    return dict(student_year=year, starting_stage=start, current_stage=current,
                stage_name=STAGE_NAMES[current], stages=stages)


def general_status(conn, user_id):
    rows = general_rows(conn, user_id)
    profile = learning_profile(conn, user_id, rows)
    eligible = [r for r in rows if r['stage'] <= profile['current_stage'] or r['progress_status']]
    progress = [r for r in eligible if r['progress_status']]
    return dict(total_words=len(eligible), new_count=len(eligible)-len(progress),
                progress_total=len(progress), reviewed_today=sum(r['reviewed_today'] for r in eligible),
                due_count=sum(bool(r['is_due']) for r in progress),
                review_pool_count=sum(r['progress_status'] in ('learning', 'fuzzy') for r in progress),
                by_status=[dict(status=s, name_zh=n, count=sum(r['progress_status']==s for r in progress))
                           for s,n in [('learning','不认识'),('fuzzy','模糊'),('known','认识')]],
                learning_profile=profile, reviewed_catalog_total=len(rows))


def select_general_rows(conn, user_id, count, review_only=False):
    rows = general_rows(conn, user_id)
    profile = learning_profile(conn, user_id, rows)
    reviews = [r for r in rows if r['progress_status'] in ('learning','fuzzy')
               and r['next_review_at'] and (review_only or (r['is_due'] and not r['reviewed_today']))]
    reviews.sort(key=lambda r: (not r['is_due'], r['next_review_at'], -(r['wrong_count'] or 0), r['id']))
    if review_only:
        return reviews[:count]
    # One headword per session; no replacement by a harder word when basics run out.
    selected, seen = [], set()
    candidates = reviews + sorted(
        [r for r in rows if not r['progress_status'] and r['stage'] <= profile['current_stage']],
        key=lambda r: (-r['stage'], r['id']))
    for row in candidates:
        if row['canonical_word'] not in seen:
            selected.append(row)
            seen.add(row['canonical_word'])
        if len(selected) >= count:
            break
    return selected
