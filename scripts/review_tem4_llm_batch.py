from __future__ import annotations

import argparse
import csv
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
REPORT_PATH = ROOT / "data" / "processed" / "question_quality" / "tem4" / "tem4_llm_review_report.csv"
UNCOMPLETABLE_PATH = ROOT / "data" / "processed" / "question_quality" / "tem4" / "tem4_uncompletable.csv"

ANSWER_FIXES = {
    (2017, 31): "C", (2017, 32): "B", (2017, 33): "B", (2017, 34): "C", (2017, 35): "A",
    (2018, 34): "B", (2018, 35): "C", (2018, 45): "B", (2018, 50): "B",
    (2018, 55): "B", (2018, 57): "C", (2018, 60): "D",
    (2024, 66): "D", (2024, 67): "C", (2024, 68): "C", (2024, 69): "B",
    (2024, 70): "A", (2024, 86): "D",
}

OPTION_CUTS = {
    (2017, 55, "D"): " РЕЧЕВОЙ ЭТИКЕТ",
    (2017, 60, "D"): " ЗАПОЛНЕНИЕ ПРОПУСКОВ",
    (2017, 90, "D"): " Писать",
    (2018, 55, "D"): " РЕЧЕВОЙ ЭТИКЕТ",
    (2018, 60, "D"): " ЗАПОЛНЕНИЕ ПРОПУСКОВ",
    (2024, 26, "B"): " --- Page",
    (2024, 65, "D"): " У НИР",
    (2024, 70, "D"): " Заполнение",
}

STEM_CUTS = {(2018, 60): " 沙拉俄语"}
SECTION_MARKERS = (
    "РЕЧЕВОЙ ЭТИКЕТ", "СТРАНОВЕДЕНИЕ", "ЛИТЕРАТУРА", "ГРАММАТИКА",
    "ЗАПОЛНЕНИЕ ПРОПУСКОВ", "ПЕРЕВОД", "СОЧИНЕНИЕ", "--- Page",
)
EXPECTED_KEYS = {"A", "B", "C", "D"}
OCR_YEARS = {2024}
LATIN_RE = re.compile(r"[A-Za-z]{2,}")
OCR_SYMBOL_RE = re.compile(r"[{}<>@#$^&*+=~|\\]")
BLANK_RE = re.compile(r"_{2,}|\.{3,}|…")


def normalize_key(value: str | None) -> str:
    value = (value or "").strip().upper()
    return {"А": "A", "В": "B", "С": "C", "Д": "D"}.get(value, value)


def clean_text(text: str, cut: str | None = None) -> str:
    value = (text or "").replace("沙拉俄语", "").strip()
    if cut and cut in value:
        value = value.split(cut, 1)[0].rstrip()
    return value


def get_questions(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT q.id, q.source_year, q.source_question_number, q.stem,
               q.correct_answer, q.review_status, qt.code AS type_code,
               p.body AS passage_body, p.id AS passage_id
        FROM questions q
        JOIN exam_systems es ON es.id = q.exam_system_id
        JOIN question_types qt ON qt.id = q.question_type_id
        LEFT JOIN passages p ON p.id = q.passage_id
        WHERE es.code = 'TEM4_RU'
        ORDER BY q.source_year, CAST(q.source_question_number AS INTEGER)
        """
    ).fetchall()


def get_options(conn: sqlite3.Connection) -> dict[int, list[sqlite3.Row]]:
    by_question: dict[int, list[sqlite3.Row]] = {}
    for row in conn.execute(
        "SELECT id, question_id, option_key, option_text, sort_order "
        "FROM question_options ORDER BY question_id, sort_order"
    ):
        by_question.setdefault(int(row["question_id"]), []).append(row)
    return by_question


def apply_text_fixes(conn: sqlite3.Connection, rows: list[sqlite3.Row], options: dict[int, list[sqlite3.Row]]) -> dict[int, list[str]]:
    changed: dict[int, list[str]] = {}
    for row in rows:
        year = int(row["source_year"])
        number = int(row["source_question_number"])
        key = (year, number)
        stem = row["stem"] or ""
        new_stem = clean_text(stem, STEM_CUTS.get(key))
        if new_stem != stem:
            conn.execute("UPDATE questions SET stem=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_stem, row["id"]))
            changed.setdefault(int(row["id"]), []).append("stem")
        for option in options.get(int(row["id"]), []):
            option_key = normalize_key(option["option_key"])
            new_text = clean_text(option["option_text"] or "", OPTION_CUTS.get((year, number, option_key)))
            if new_text != (option["option_text"] or ""):
                conn.execute("UPDATE question_options SET option_text=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_text, option["id"]))
                changed.setdefault(int(row["id"]), []).append("option_" + option_key)
        if key in ANSWER_FIXES and normalize_key(row["correct_answer"]) != ANSWER_FIXES[key]:
            conn.execute("UPDATE questions SET correct_answer=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (ANSWER_FIXES[key], row["id"]))
            changed.setdefault(int(row["id"]), []).append("correct_answer")
    return changed


def readiness(row: sqlite3.Row, option_rows: list[sqlite3.Row]) -> tuple[str, str]:
    type_code = row["type_code"]
    if type_code == "listening_choice":
        return "keep_needs_review", "听力题缺少可核验的题干和音频绑定，需完成听力材料与转写审核"
    if int(row["source_year"]) in OCR_YEARS:
        return "keep_needs_review", "2024 年题目来自 OCR，需人工逐题核对原 PDF 后才能进入练习"
    if type_code == "reading_choice":
        return "keep_needs_review", "阅读文章需逐篇核对清洁 OCR、题干、选项和答案，当前不能只凭结构放行"

    texts = [row["stem"] or ""] + [(x["option_text"] or "") for x in option_rows]
    stem = row["stem"] or ""
    answer = normalize_key(row["correct_answer"])
    keys = [normalize_key(x["option_key"]) for x in option_rows]
    if len(option_rows) != 4:
        return "keep_needs_review", f"选项数量为 {len(option_rows)}，不是四项"
    if set(keys) != EXPECTED_KEYS or len(set(keys)) != 4:
        return "keep_needs_review", "选项编号不完整或重复"
    if any(not (x["option_text"] or "").strip() for x in option_rows):
        return "keep_needs_review", "存在空选项"
    if not answer or answer not in EXPECTED_KEYS or answer not in keys:
        return "keep_needs_review", "缺少可靠答案或答案不在选项中"
    if len(stem.strip()) < 18:
        return "keep_needs_review", "题干过短，疑似切分失败"
    joined = " ".join(texts)
    if "�" in joined:
        return "keep_needs_review", "存在替换乱码字符"
    if "沙拉俄语" in joined:
        return "keep_needs_review", "仍残留水印文本"
    if any(marker.lower() in joined.lower() for marker in SECTION_MARKERS):
        return "keep_needs_review", "仍含页脚、章节标题或分页标记"
    if LATIN_RE.search(joined):
        return "keep_needs_review", "俄语题目中混入连续拉丁字符，需人工核对"
    if OCR_SYMBOL_RE.search(joined):
        return "keep_needs_review", "存在疑似 OCR 特殊符号"
    if any(len((x["option_text"] or "").strip()) > 140 for x in option_rows):
        return "keep_needs_review", "选项过长，疑似吸收页脚或下一题内容"
    if type_code == "grammar_choice" and not BLANK_RE.search(stem):
        return "keep_needs_review", "语法题填空位置不明确"
    return "approve", "题干、四个选项、答案和题型结构完整，未发现当前规则识别出的 OCR/页脚风险"


def main() -> None:
    parser = argparse.ArgumentParser(description="Conservative local LLM review for TEM4.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--uncompletable", type=Path, default=UNCOMPLETABLE_PATH)
    args = parser.parse_args()

    backup = args.db.parent.parent / "data" / "processed" / "backups" / (
        "russian_ai_tutor_before_tem4_batch_review_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".sqlite"
    )
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.db, backup)

    with sqlite3.connect(args.db) as conn:
        conn.row_factory = sqlite3.Row
        rows = get_questions(conn)
        options = get_options(conn)
        changed = apply_text_fixes(conn, rows, options)
        rows = get_questions(conn)
        options = get_options(conn)
        report_rows: list[dict[str, Any]] = []
        for row in rows:
            decision, reason = readiness(row, options.get(int(row["id"]), []))
            if decision == "approve":
                status = "approved"
                conn.execute(
                    "UPDATE questions SET review_status='approved', source_usage='practice', content_origin='past_exam_original', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (row["id"],),
                )
            else:
                status = "needs_review"
                conn.execute(
                    "UPDATE questions SET review_status='needs_review', source_usage='source_reference_only', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (row["id"],),
                )
            fields = ",".join(changed.get(int(row["id"]), []))
            if fields:
                reason += "; changed=" + fields
            conn.execute(
                "INSERT INTO question_review_logs (question_id, review_decision, review_notes, reviewer) VALUES (?, ?, ?, 'local_llm_tem4_batch_review')",
                (row["id"], "approved" if decision == "approve" else "needs_review", reason),
            )
            report_rows.append({
                "question_id": row["id"],
                "source_year": row["source_year"],
                "source_question_number": row["source_question_number"],
                "question_type": row["type_code"],
                "decision": decision,
                "review_status": status,
                "changed_fields": fields,
                "reason": reason,
            })
        conn.commit()

    for path, data in ((args.report, report_rows), (args.uncompletable, [x for x in report_rows if x["decision"] != "approve"])):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(report_rows[0]))
            writer.writeheader()
            writer.writerows(data)

    by_year: dict[str, dict[str, int]] = {}
    for row in report_rows:
        bucket = by_year.setdefault(str(row["source_year"]), {"approved": 0, "needs_review": 0})
        bucket[row["review_status"]] += 1
    print({
        "backup": str(backup),
        "total": len(report_rows),
        "approved": sum(x["review_status"] == "approved" for x in report_rows),
        "needs_review": sum(x["review_status"] == "needs_review" for x in report_rows),
        "by_year": by_year,
        "report": str(args.report),
        "uncompletable": str(args.uncompletable),
    })


if __name__ == "__main__":
    main()


