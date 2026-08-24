from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "database" / "russian_ai_tutor.sqlite"
REPORT_DIR = ROOT / "data" / "processed" / "words"
BACKUP_DIR = ROOT / "data" / "processed" / "backups"


KNOWN_FIXES: dict[str, dict[str, str]] = {
    "консерватбрия": {
        "word": "консерватория",
        "lemma": "консерватория",
        "part_of_speech": "阴",
        "meaning_zh": "音乐学院",
        "reason": "OCR 把 о 识别为 б。",
    },
    "индустриальный": {
        "word": "индустриальный",
        "lemma": "индустриальный",
        "part_of_speech": "形",
        "meaning_zh": "工业的；产业的",
        "reason": "原释义只有文体标记“(书)”，缺失核心词义。",
    },
    "разочарование": {
        "word": "разочарование",
        "lemma": "разочарование",
        "part_of_speech": "中",
        "meaning_zh": "失望；扫兴",
        "reason": "OCR 把“兴”识别为“六”。",
    },
    "неведомый": {
        "word": "неведомый",
        "lemma": "неведомый",
        "part_of_speech": "形",
        "meaning_zh": "未知的；人所不知的；神秘的",
        "reason": "补全常见核心释义。",
    },
    "откуда-то": {
        "word": "откуда-то",
        "lemma": "откуда-то",
        "part_of_speech": "副",
        "meaning_zh": "不知从哪里；从某处",
        "reason": "修正中文 OCR 错字并统一分号。",
    },
    "откуда-нибудь": {
        "word": "откуда-нибудь",
        "lemma": "откуда-нибудь",
        "part_of_speech": "副",
        "meaning_zh": "从随便什么地方；不管从哪里",
        "reason": "修正中文 OCR 错字并统一分号。",
    },
    "будка": {
        "word": "будка",
        "lemma": "будка",
        "part_of_speech": "阴",
        "meaning_zh": "岗亭；小室",
        "reason": "清除中文释义 OCR 污染。",
    },
}

BAD_MEANING_MARKERS = [
    "扫六",
    "哨里",
    "晨里",
    "岗楹",
    "哨史",
    "��",
    "�",
]

BAD_WORD_PATTERNS = [
    ("брия", "词形可能把 о 识别为 б"),
    ("сбф", "词形可能把 о 识别为 б"),
    ("бф", "词形可能把 о 识别为 б"),
]


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def has_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def is_thin_meaning(meaning: str) -> bool:
    text = clean(meaning)
    if not text:
        return True
    if text in {"(书)", "（书）", "(口)", "（口）"}:
        return True
    without_marks = re.sub(r"[()（）书口转俗旧雅]", "", text)
    if len(without_marks) <= 1:
        return True
    if len(text) <= 3 and has_chinese(text):
        return True
    return False


def audit_row(row: sqlite3.Row) -> dict[str, str] | None:
    word = clean(row["word"])
    meaning = clean(row["meaning_zh"])
    issues: list[str] = []
    suggested = KNOWN_FIXES.get(word)

    if suggested:
        issues.append("known_fix")
    if is_thin_meaning(meaning):
        issues.append("meaning_too_thin")
    for marker in BAD_MEANING_MARKERS:
        if marker in meaning:
            issues.append(f"bad_meaning_marker:{marker}")
    for pattern, note in BAD_WORD_PATTERNS:
        if pattern in word:
            issues.append(f"bad_word_pattern:{pattern}:{note}")
    if not has_chinese(meaning):
        issues.append("meaning_has_no_chinese")
    if not issues:
        return None

    return {
        "id": str(row["id"]),
        "word": word,
        "lemma": clean(row["lemma"]),
        "part_of_speech": clean(row["part_of_speech"]),
        "meaning_zh": meaning,
        "issues": "；".join(issues),
        "suggested_word": suggested["word"] if suggested else "",
        "suggested_lemma": suggested["lemma"] if suggested else "",
        "suggested_part_of_speech": suggested["part_of_speech"] if suggested else "",
        "suggested_meaning_zh": suggested["meaning_zh"] if suggested else "",
        "suggestion_reason": suggested["reason"] if suggested else "",
        "review_decision": "auto_fix_available" if suggested else "needs_llm_or_manual_review",
    }


def backup_db(db_path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / f"{db_path.stem}_before_vocab_audit_fixes_{stamp}.sqlite"
    shutil.copy2(db_path, target)
    return target


def apply_known_fixes(conn: sqlite3.Connection, report_rows: list[dict[str, str]]) -> int:
    fixed = 0
    for row in report_rows:
        if row["review_decision"] != "auto_fix_available":
            continue
        item_id = int(row["id"])
        collision = conn.execute(
            """
            SELECT id
            FROM vocabulary_items
            WHERE id <> ?
              AND word = ?
              AND COALESCE(part_of_speech, '') = COALESCE(?, '')
            LIMIT 1
            """,
            (item_id, row["suggested_word"], row["suggested_part_of_speech"]),
        ).fetchone()
        if collision:
            row["review_decision"] = "needs_manual_review_collision"
            continue
        conn.execute(
            """
            UPDATE vocabulary_items
            SET word = ?, lemma = ?, part_of_speech = ?, meaning_zh = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                row["suggested_word"],
                row["suggested_lemma"] or None,
                row["suggested_part_of_speech"] or None,
                row["suggested_meaning_zh"],
                item_id,
            ),
        )
        fixed += 1
    return fixed


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "id",
        "word",
        "lemma",
        "part_of_speech",
        "meaning_zh",
        "issues",
        "suggested_word",
        "suggested_lemma",
        "suggested_part_of_speech",
        "suggested_meaning_zh",
        "suggestion_reason",
        "review_decision",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_llm_payload(path: Path, rows: list[dict[str, str]]) -> None:
    payload = {
        "task": "请作为俄语词典校对助手，逐条检查俄文词形、词性和中文释义。修正 OCR 错误，补全核心中文义项。不要编造不确定内容；不确定则标记 needs_manual_review。",
        "output_schema": {
            "id": "原 id",
            "status": "approved | needs_manual_review | reject",
            "corrected_word": "修正后的俄文词",
            "corrected_lemma": "原形，可空",
            "corrected_part_of_speech": "中文词性简称，可空",
            "corrected_meaning_zh": "准确、简洁、较完整的中文核心释义",
            "notes": "说明修改原因",
        },
        "items": [
            {
                "id": row["id"],
                "word": row["word"],
                "lemma": row["lemma"],
                "part_of_speech": row["part_of_speech"],
                "meaning_zh": row["meaning_zh"],
                "issues": row["issues"],
            }
            for row in rows
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit and improve approved vocabulary rows.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--apply-known", action="store_true", help="Apply high-confidence built-in fixes.")
    parser.add_argument("--llm-payload-limit", type=int, default=200, help="How many flagged rows to include in the LLM payload JSON.")
    args = parser.parse_args()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"vocabulary_semantic_audit_{stamp}.csv"
    llm_payload_path = REPORT_DIR / f"vocabulary_llm_audit_payload_{stamp}.json"

    with connect(args.db) as conn:
        rows = conn.execute(
            """
            SELECT id, word, lemma, part_of_speech, meaning_zh
            FROM vocabulary_items
            WHERE review_status = 'approved'
            ORDER BY id
            """
        ).fetchall()
        report_rows = [item for row in rows if (item := audit_row(row))]
        backup_path = None
        fixed = 0
        if args.apply_known and report_rows:
            backup_path = backup_db(args.db)
            fixed = apply_known_fixes(conn, report_rows)
            conn.commit()

    write_csv(report_path, report_rows)
    write_llm_payload(llm_payload_path, report_rows[: max(0, args.llm_payload_limit)])
    summary = {
        "approved_words_checked": len(rows),
        "flagged_rows": len(report_rows),
        "known_fixes_applied": fixed,
        "backup": str(backup_path) if backup_path else "",
        "audit_report": str(report_path),
        "llm_payload": str(llm_payload_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
