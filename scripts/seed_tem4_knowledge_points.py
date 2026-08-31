from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from seed_tem8_knowledge_points import POINTS as SHARED_POINTS


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"

LISTENING_POINT = (
    "listening",
    None,
    "听力理解",
    "Аудирование",
    "listening",
    "俄语专四听力理解能力。听力题完成音频绑定和人工校对前不进入正式练习池。",
    10,
)

# TEM4 currently has no literature section in the formal practice pool.
POINTS = [
    LISTENING_POINT,
    *[
        (
            code,
            parent,
            name_zh,
            name_ru,
            category,
            description.replace("专八", "专四"),
            sort_order,
        )
        for code, parent, name_zh, name_ru, category, description, sort_order in SHARED_POINTS
        if category in {"grammar", "culture", "reading"}
    ],
]


def exam_system_id(conn: sqlite3.Connection) -> int:
    conn.execute(
        """
        INSERT OR IGNORE INTO exam_systems (code, name_zh, name_original, description)
        VALUES ('TEM4_RU', '俄语专业四级', 'Русский язык TEM-4', '俄语专四题库')
        """
    )
    system_id = int(conn.execute("SELECT id FROM exam_systems WHERE code = 'TEM4_RU'").fetchone()[0])
    conn.execute(
        """
        INSERT OR IGNORE INTO exam_levels (exam_system_id, code, name_zh, sort_order)
        VALUES (?, 'TEM4', '专四', 1)
        """,
        (system_id,),
    )
    return system_id


def seed(db_path: Path = DB_PATH) -> dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        system_id = exam_system_id(conn)
        ids = {
            str(code): int(point_id)
            for code, point_id in conn.execute(
                "SELECT code, id FROM knowledge_points WHERE exam_system_id = ?",
                (system_id,),
            )
        }

        for code, parent_code, name_zh, name_ru, category, description, sort_order in POINTS:
            parent_id = ids.get(parent_code) if parent_code else None
            row = conn.execute(
                "SELECT id FROM knowledge_points WHERE exam_system_id = ? AND code = ?",
                (system_id, code),
            ).fetchone()
            if row:
                point_id = int(row[0])
                conn.execute(
                    """
                    UPDATE knowledge_points
                    SET parent_id = ?, name_zh = ?, name_ru = ?, category = ?,
                        description = ?, sort_order = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (parent_id, name_zh, name_ru, category, description, sort_order, point_id),
                )
            else:
                point_id = int(
                    conn.execute(
                        """
                        INSERT INTO knowledge_points (
                          exam_system_id, parent_id, code, name_zh, name_ru,
                          category, description, sort_order
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (system_id, parent_id, code, name_zh, name_ru, category, description, sort_order),
                    ).lastrowid
                )
            ids[code] = point_id

        conn.commit()
        counts = [
            {"category": category, "count": int(count)}
            for category, count in conn.execute(
                """
                SELECT category, COUNT(*)
                FROM knowledge_points
                WHERE exam_system_id = ?
                GROUP BY category
                ORDER BY category
                """,
                (system_id,),
            )
        ]
    return {"exam_system": "TEM4_RU", "seeded": len(POINTS), "counts": counts}


def main() -> None:
    print(json.dumps(seed(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
