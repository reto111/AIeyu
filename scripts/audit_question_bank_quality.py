from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
OUT_DIR = ROOT / "data" / "processed" / "question_quality"

EXPECTED_KEYS = {"A", "B", "C", "D"}
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
LATIN_RE = re.compile(r"[A-Za-z]{2,}")
OCR_SYMBOL_RE = re.compile(r"(SS|THB|XY|[{}[\]<>@#$^&*+=~`|\\])")
SECTION_NOISE_RE = re.compile(
    r"(СТРАНОВЕДЕНИЕ|ЛИТЕРАТУРА|ГРАММАТИКА|201[0-9]\s*\+|IS Sl|rk EMS|Bk EMR|Rae \(2008)",
    re.I,
)
PAGE_NOISE_RE = re.compile(r"(\b\d{3,4}\b\s+[A-Za-z]{2,}|\b[A-Za-z]{2,}\s+\d{3,4}\b)")
OPTION_MARKER_LINE_RE = re.compile(r"(?m)^\s*([АAВBСCДD]\)|[АAВBСCДD]\.)\s+")
INITIAL_ONLY_RE = re.compile(r"^[А-ЯЁA-Z]\.?$")


def normalize_key(key: str) -> str:
    key = (key or "").strip().upper()
    return {"А": "A", "В": "B", "С": "C", "Д": "D"}.get(key, key)


def text_len(text: str | None) -> int:
    return len((text or "").strip())


def has_latin_noise(text: str | None) -> bool:
    text = text or ""
    for token in LATIN_RE.findall(text):
        upper = token.upper()
        if re.fullmatch(r"[IVXLCDM]+", upper):
            continue
        if upper in {"RF", "USA", "USSR", "TV", "DVD", "CD", "USB"}:
            continue
        return True
    return False


def add_issue(issues: list[dict], row: sqlite3.Row, severity: str, code: str, detail: str) -> None:
    issues.append(
        {
            "severity": severity,
            "issue_code": code,
            "question_id": row["id"],
            "source_year": row["source_year"] or "",
            "source_question_number": row["source_question_number"] or "",
            "type_code": row["type_code"],
            "review_status": row["review_status"],
            "source_usage": row["source_usage"],
            "detail": detail,
            "stem_preview": (row["stem"] or "").replace("\n", " ")[:180],
        }
    )


def load_questions(con: sqlite3.Connection) -> list[sqlite3.Row]:
    return con.execute(
        """
        select
            q.*,
            qt.code as type_code,
            p.body as passage_body,
            p.title as passage_title
        from questions q
        join question_types qt on qt.id = q.question_type_id
        left join passages p on p.id = q.passage_id
        order by coalesce(q.source_year, 9999), cast(q.source_question_number as integer), q.id
        """
    ).fetchall()


def load_options(con: sqlite3.Connection) -> dict[int, list[sqlite3.Row]]:
    by_question: dict[int, list[sqlite3.Row]] = {}
    rows = con.execute(
        """
        select question_id, option_key, option_text, sort_order
        from question_options
        order by question_id, sort_order, option_key
        """
    ).fetchall()
    for row in rows:
        by_question.setdefault(row["question_id"], []).append(row)
    return by_question


def audit_question(row: sqlite3.Row, options: list[sqlite3.Row]) -> list[dict]:
    issues: list[dict] = []
    stem = row["stem"] or ""
    type_code = row["type_code"]
    option_keys = [normalize_key(opt["option_key"]) for opt in options]
    option_texts = [opt["option_text"] or "" for opt in options]

    if row["review_status"] == "approved" and len(options) != 4:
        add_issue(issues, row, "high", "option_count_not_4", f"选项数量为 {len(options)}，不是 4。")

    missing_keys = sorted(EXPECTED_KEYS - set(option_keys))
    if row["review_status"] == "approved" and missing_keys:
        add_issue(issues, row, "high", "missing_option_key", "缺少选项：" + ",".join(missing_keys))

    correct = normalize_key(row["correct_answer"] or "")
    if correct and correct not in set(option_keys):
        add_issue(issues, row, "high", "correct_answer_missing_option", f"正确答案 {correct} 不在选项中。")

    if type_code != "reading_choice" and text_len(stem) < 18:
        add_issue(issues, row, "high", "stem_too_short", "非阅读题题干过短，疑似切分失败。")

    if type_code in {"grammar_choice", "literature_choice", "culture_choice"}:
        if has_latin_noise(stem) and CYRILLIC_RE.search(stem):
            add_issue(issues, row, "medium", "stem_has_latin_noise", "俄语题干中夹杂连续拉丁字母，疑似 OCR 噪声。")
        if OCR_SYMBOL_RE.search(stem):
            add_issue(issues, row, "medium", "stem_has_ocr_symbols", "题干含常见 OCR 噪声符号或错误片段。")
        if not any(marker in stem for marker in ("____", "...", "…", " .", " — ")) and text_len(stem) > 24:
            add_issue(issues, row, "low", "blank_marker_missing_likely", "选择填空题可能缺少显式空格标记。")

    if OPTION_MARKER_LINE_RE.search(stem):
        add_issue(issues, row, "medium", "option_marker_inside_stem", "题干中疑似残留选项编号。")

    if SECTION_NOISE_RE.search(stem) or SECTION_NOISE_RE.search(" ".join(option_texts)):
        add_issue(issues, row, "medium", "section_or_footer_noise", "题干或选项中含页脚/栏目标题噪声。")

    for opt in options:
        key = normalize_key(opt["option_key"])
        text = opt["option_text"] or ""
        if text_len(text) == 0:
            add_issue(issues, row, "high", "empty_option_text", f"{key} 选项为空。")
        if type_code in {"literature_choice", "culture_choice"} and INITIAL_ONLY_RE.fullmatch(text.strip()):
            add_issue(issues, row, "high", "option_author_initial_fragment", f"{key} 选项只有单个首字母，作者姓名可能被切断。")
        if text_len(text) > 140:
            add_issue(issues, row, "medium", "option_text_too_long", f"{key} 选项过长，可能吸收题干或页脚。")
        if SECTION_NOISE_RE.search(text) or PAGE_NOISE_RE.search(text):
            add_issue(issues, row, "medium", "option_contains_noise", f"{key} 选项含页码、栏目标题或页脚噪声。")
        if OCR_SYMBOL_RE.search(text):
            add_issue(issues, row, "medium", "option_has_ocr_symbols", f"{key} 选项含常见 OCR 噪声。")
        if has_latin_noise(text) and CYRILLIC_RE.search(text):
            add_issue(issues, row, "medium", "option_has_latin_noise", f"{key} 俄语选项夹杂拉丁字母，疑似 OCR 乱码。")

    if text_len(stem) < 16 and any(text_len(text) > 50 for text in option_texts):
        add_issue(issues, row, "high", "author_initial_split_risk", "题干极短且选项过长，可能把 В.Г. 等作者缩写误切成 B 选项。")

    if type_code == "reading_choice":
        passage = row["passage_body"] or ""
        if not row["passage_id"] or text_len(passage) < 300:
            add_issue(issues, row, "high", "reading_passage_missing_or_short", "阅读题缺少文章或文章长度异常短。")
        if OPTION_MARKER_LINE_RE.search(passage):
            add_issue(issues, row, "medium", "reading_passage_contains_option_marker", "阅读文章中疑似残留题号或选项编号。")
        if has_latin_noise(passage) and CYRILLIC_RE.search(passage):
            add_issue(issues, row, "low", "reading_passage_has_latin_noise", "阅读文章中夹杂连续拉丁字母，需要抽查是否为 OCR 噪声。")

    return issues


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "severity",
        "issue_code",
        "question_id",
        "source_year",
        "source_question_number",
        "type_code",
        "review_status",
        "source_usage",
        "detail",
        "stem_preview",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit structured question bank quality.")
    parser.add_argument("--db", default=str(DB_PATH), help="SQLite database path.")
    parser.add_argument("--out-dir", default=str(OUT_DIR), help="Output directory.")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    questions = load_questions(con)
    options = load_options(con)

    issues: list[dict] = []
    for row in questions:
        issues.extend(audit_question(row, options.get(row["id"], [])))

    severity_order = {"high": 0, "medium": 1, "low": 2}
    issues.sort(
        key=lambda item: (
            severity_order.get(item["severity"], 9),
            str(item["source_year"]),
            int(item["source_question_number"] or 9999) if str(item["source_question_number"]).isdigit() else 9999,
            item["issue_code"],
        )
    )

    manual_review = [
        item
        for item in issues
        if item["severity"] in {"high", "medium"}
        and (
            item["review_status"] == "approved"
            or item["source_usage"] == "source_reference_only"
            or item["source_year"]
        )
    ]

    summary = {
        "database": str(Path(args.db).resolve()),
        "question_count": len(questions),
        "issue_count": len(issues),
        "manual_review_count": len(manual_review),
        "by_severity": dict(Counter(item["severity"] for item in issues)),
        "by_issue_code": dict(Counter(item["issue_code"] for item in issues)),
        "by_type_code": dict(Counter(item["type_code"] for item in issues)),
    }

    write_csv(out_dir / "question_quality_audit.csv", issues)
    write_csv(out_dir / "question_quality_manual_review.csv", manual_review)
    (out_dir / "question_quality_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
