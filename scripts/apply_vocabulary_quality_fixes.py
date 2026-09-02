from __future__ import annotations

import argparse
import csv
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "database" / "russian_ai_tutor.sqlite"
BACKUP_DIR = ROOT / "data" / "processed" / "backups"
REPORT_DIR = ROOT / "data" / "processed" / "words"

WORD_FIXES = [
    {
        "old_word": "филосбфский",
        "new_word": "философский",
        "new_lemma": "философский",
        "part_of_speech": "形",
        "meaning_zh": "哲学的",
        "reason": "OCR 把 о 识别成 б。",
    },
]

MEANING_FIXES = [
    {
        "word": "откуда-то",
        "meaning_zh": "不知从哪里, 从某处",
        "reason": "OCR 把 哪里 识别成 哨里。",
    },
    {
        "word": "откуда-нибудь",
        "meaning_zh": "从随便什么地方, 不管从哪里",
        "reason": "OCR 把 哪里 识别成 晨里。",
    },
    {
        "word": "будка",
        "meaning_zh": "岗亭；小室",
        "reason": "中文释义 OCR 串入错字。",
    },
    {
        "word": "набор",
        "meaning_zh": "招收；一套",
        "reason": "中文释义末尾重复混入俄语词头。",
    },
    {
        "word": "претензия",
        "meaning_zh": "要求；主张",
        "reason": "中文释义末尾重复混入俄语词头。",
    },
]

SUSPICIOUS_MEANING_MARKERS = ["哨里", "晨里", "岗楹", "哨史"]
SUSPICIOUS_WORD_MARKERS = ["сбф", "бф"]


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def backup_db(db_path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{db_path.stem}_before_vocab_quality_fixes_{stamp}.sqlite"
    shutil.copy2(db_path, backup_path)
    return backup_path


def apply_word_fixes(conn: sqlite3.Connection) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    for fix in WORD_FIXES:
        rows = conn.execute(
            """
            SELECT id, word, lemma, part_of_speech, meaning_zh
            FROM vocabulary_items
            WHERE word = ?
            """,
            (fix["old_word"],),
        ).fetchall()
        for row in rows:
            collision = conn.execute(
                """
                SELECT id
                FROM vocabulary_items
                WHERE id <> ?
                  AND word = ?
                  AND COALESCE(part_of_speech, '') = COALESCE(?, '')
                LIMIT 1
                """,
                (row["id"], fix["new_word"], fix["part_of_speech"]),
            ).fetchone()
            if collision:
                changes.append(
                    {
                        "id": str(row["id"]),
                        "word": row["word"],
                        "action": "skipped_collision",
                        "detail": f"目标词已存在：{fix['new_word']}",
                    }
                )
                continue
            conn.execute(
                """
                UPDATE vocabulary_items
                SET word = ?, lemma = ?, part_of_speech = ?, meaning_zh = ?
                WHERE id = ?
                """,
                (
                    fix["new_word"],
                    fix["new_lemma"],
                    fix["part_of_speech"],
                    fix["meaning_zh"],
                    row["id"],
                ),
            )
            changes.append(
                {
                    "id": str(row["id"]),
                    "word": row["word"],
                    "action": "updated_word",
                    "detail": f"{row['word']} -> {fix['new_word']}；{fix['reason']}",
                }
            )
    return changes


def apply_meaning_fixes(conn: sqlite3.Connection) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    for fix in MEANING_FIXES:
        rows = conn.execute(
            """
            SELECT id, word, meaning_zh
            FROM vocabulary_items
            WHERE word = ?
            """,
            (fix["word"],),
        ).fetchall()
        for row in rows:
            if row["meaning_zh"] == fix["meaning_zh"]:
                continue
            conn.execute(
                """
                UPDATE vocabulary_items
                SET meaning_zh = ?
                WHERE id = ?
                """,
                (fix["meaning_zh"], row["id"]),
            )
            changes.append(
                {
                    "id": str(row["id"]),
                    "word": row["word"],
                    "action": "updated_meaning",
                    "detail": f"{row['meaning_zh']} -> {fix['meaning_zh']}；{fix['reason']}",
                }
            )
    return changes


def collect_suspicious_rows(conn: sqlite3.Connection) -> list[dict[str, str]]:
    rows = conn.execute(
        """
        SELECT id, word, lemma, part_of_speech, meaning_zh
        FROM vocabulary_items
        WHERE review_status = 'approved'
        ORDER BY id
        """
    ).fetchall()
    suspicious: list[dict[str, str]] = []
    for row in rows:
        issues = []
        word = row["word"] or ""
        meaning = row["meaning_zh"] or ""
        for marker in SUSPICIOUS_WORD_MARKERS:
            if marker in word:
                issues.append(f"词形疑似 OCR：{marker}")
        for marker in SUSPICIOUS_MEANING_MARKERS:
            if marker in meaning:
                issues.append(f"释义疑似 OCR：{marker}")
        if not issues:
            continue
        suspicious.append(
            {
                "id": str(row["id"]),
                "word": word,
                "lemma": row["lemma"] or "",
                "part_of_speech": row["part_of_speech"] or "",
                "meaning_zh": meaning,
                "issue": "；".join(issues),
            }
        )
    return suspicious


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    db_path = args.db
    backup_path = backup_db(db_path)
    with connect(db_path) as conn:
        changes = apply_word_fixes(conn)
        changes.extend(apply_meaning_fixes(conn))
        suspicious = collect_suspicious_rows(conn)
        conn.commit()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    changes_path = REPORT_DIR / f"vocabulary_quality_fixes_{stamp}.csv"
    suspicious_path = REPORT_DIR / f"vocabulary_quality_suspicious_{stamp}.csv"
    write_csv(changes_path, changes, ["id", "word", "action", "detail"])
    write_csv(suspicious_path, suspicious, ["id", "word", "lemma", "part_of_speech", "meaning_zh", "issue"])
    print(f"backup={backup_path}")
    print(f"changes={len(changes)} report={changes_path}")
    print(f"suspicious_remaining={len(suspicious)} report={suspicious_path}")


if __name__ == "__main__":
    main()
