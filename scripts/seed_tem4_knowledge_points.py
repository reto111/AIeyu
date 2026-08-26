from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'database' / 'russian_ai_tutor.sqlite'
POINTS = [
    ('listening', '听力理解', 'Аудирование', 'listening', 1),
    ('grammar', '语法与词汇', 'Грамматика и лексика', 'grammar', 2),
    ('culture', '言语交际与国情', 'Речевой этикет и страноведение', 'culture', 3),
    ('reading', '阅读理解', 'Чтение', 'reading', 4),
]


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute("INSERT OR IGNORE INTO exam_systems (code,name_zh,name_original,description) VALUES ('TEM4_RU','俄语专业四级','Русский язык TEM-4','俄语专四题库')")
        system_id = int(conn.execute("SELECT id FROM exam_systems WHERE code='TEM4_RU'").fetchone()[0])
        conn.execute("INSERT OR IGNORE INTO exam_levels (exam_system_id,code,name_zh,sort_order) VALUES (?, 'TEM4', '专四', 1)", (system_id,))
        for code, name_zh, name_ru, category, sort_order in POINTS:
            conn.execute(
                """INSERT INTO knowledge_points (exam_system_id, parent_id, code, name_zh, name_ru, category, description, sort_order)
                   VALUES (?, NULL, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(exam_system_id, code) DO UPDATE SET name_zh=excluded.name_zh, name_ru=excluded.name_ru,
                   category=excluded.category, description=excluded.description, sort_order=excluded.sort_order,
                   updated_at=CURRENT_TIMESTAMP""",
                (system_id, code, name_zh, name_ru, category, f'俄语专四第一版 {name_zh} 粗粒度知识点', sort_order),
            )
        conn.commit()
        rows = conn.execute("SELECT code,name_zh FROM knowledge_points WHERE exam_system_id=? ORDER BY sort_order", (system_id,)).fetchall()
    print(json.dumps({'exam_system': 'TEM4_RU', 'knowledge_points': [dict(zip(['code','name_zh'], row)) for row in rows]}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
