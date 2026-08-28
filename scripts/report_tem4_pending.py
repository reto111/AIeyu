from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "words" / "tem4_words_review_simple.csv"
OUTPUT = ROOT / "data" / "processed" / "words" / "tem4_pending_review_list.csv"
SUMMARY_JSON = ROOT / "data" / "processed" / "words" / "tem4_pending_review_summary.json"
SUMMARY_MD = ROOT / "data" / "processed" / "words" / "tem4_pending_review_summary.md"


CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
CHINESE_RE = re.compile(r"[\u3400-\u9fff]")
LATIN_RE = re.compile(r"[A-Za-z]")
VALID_WORD_RE = re.compile(r"[А-Яа-яЁё]+(?:[-'][А-Яа-яЁё]+)*")
NOISE_RE = re.compile(r"[�□]|[№]|[|\\]|\d")


def has_cyrillic(value: str) -> bool:
    return bool(CYRILLIC_RE.search(value or ""))


def has_chinese(value: str) -> bool:
    return bool(CHINESE_RE.search(value or ""))


def classify(row: dict[str, str]) -> tuple[str, list[str], str]:
    word = (row.get("word") or "").strip()
    original = (row.get("original_word") or "").strip()
    meaning = (row.get("meaning_zh") or "").strip()
    raw_headword = (row.get("raw_headword") or "").strip()
    raw_block = (row.get("raw_block") or "").strip()
    auto_notes = (row.get("auto_notes") or "").strip()
    parse_status = (row.get("parse_status") or "").strip()
    review_notes = (row.get("review_notes") or "").strip()

    flags: list[str] = []
    reasons: list[str] = []

    if not VALID_WORD_RE.fullmatch(word) or has_cyrillic(word) is False:
        flags.append("词头疑似OCR错误")
        reasons.append("词头含拉丁字母、数字、异常符号，或无法构成完整俄语词")
    if word != original and original:
        flags.append("词头已被自动改写")
        reasons.append("当前词头与原始识别结果不同，需要确认自动修正是否正确")
    if "latin_digit_ocr_transliterated" in auto_notes:
        flags.append("拉丁/数字OCR转写")
        reasons.append("词头曾由拉丁字母或数字转写，需核对俄文字母形状")
    if "fallback_first_cyrillic_token" in auto_notes:
        flags.append("疑似抓取了首个俄文片段")
        reasons.append("解析器只能抓取原始块中的第一个俄文片段，可能发生切分错位")
    if "missing_chinese_meaning" in auto_notes or not has_chinese(meaning):
        flags.append("释义缺失或不完整")
        reasons.append("没有可确认的中文核心释义，或释义长度过短")
    if has_cyrillic(meaning) or LATIN_RE.search(meaning) or NOISE_RE.search(meaning):
        flags.append("释义含OCR噪声")
        reasons.append("中文释义中混入俄文、拉丁字母、数字或异常符号，可能带入例句/乱码")
    if len(re.findall(r"[\u3400-\u9fff]", meaning)) < 2:
        flags.append("释义信息不足")
        reasons.append("中文信息量过少，无法直接作为正式词义")

    lower_raw = f"{raw_headword} {raw_block}".lower()
    if parse_status == "needs_review" or "fragment" in lower_raw or "continuation" in lower_raw or "续" in raw_block:
        flags.append("解析或边界无法确认")
        reasons.append("解析器无法可靠确定词头/释义边界，需要结合原始页面确认")

    if "stressed_i_ocr" in auto_notes or "visual_uppercase_noise_normalized" in auto_notes:
        flags.append("字母形状需复核")
        reasons.append("OCR曾对重音字母或大小写视觉噪声做归一化，需复核词形")
    if "ocr_audit_suggested_medium" in review_notes or row.get("auto_confidence") in {"medium", "low"}:
        flags.append("置信度不足")
        reasons.append("自动审核置信度为中/低，不能直接进入正式词库")

    # Priority is intentionally conservative: a questionable boundary or word form
    # takes precedence over a merely overlong OCR definition.
    if "解析或边界无法确认" in flags:
        issue_type = "解析/边界疑点"
    elif any("词头" in f or "字母" in f or "拉丁" in f for f in flags):
        issue_type = "词头或字母疑点"
    elif any("释义" in f for f in flags):
        issue_type = "释义疑点"
    elif "置信度不足" in flags:
        issue_type = "低置信度"
    else:
        issue_type = "需人工确认"

    if not flags:
        flags.append("待最终确认")
        reasons.append("未命中明显规则，但当前状态仍为pending，暂不自动入库")

    return issue_type, flags, "；".join(dict.fromkeys(reasons))


def main() -> None:
    with INPUT.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("review_status") == "pending"]

    output_rows: list[dict[str, str]] = []
    category_counts: Counter[str] = Counter()
    flag_counts: Counter[str] = Counter()
    for index, row in enumerate(rows, 1):
        issue_type, flags, reason = classify(row)
        category_counts[issue_type] += 1
        flag_counts.update(flags)
        output_rows.append(
            {
                "pending_index": str(index),
                "source_file": row.get("source_file", ""),
                "source_page": row.get("source_page", ""),
                "block_index": row.get("block_index", ""),
                "word": row.get("word", ""),
                "original_word": row.get("original_word", ""),
                "lemma": row.get("lemma", ""),
                "part_of_speech": row.get("part_of_speech", ""),
                "meaning_zh": row.get("meaning_zh", ""),
                "auto_confidence": row.get("auto_confidence", ""),
                "parse_status": row.get("parse_status", ""),
                "issue_type": issue_type,
                "issue_flags": "；".join(flags),
                "issue_reason": reason,
                "auto_notes": row.get("auto_notes", ""),
                "review_notes": row.get("review_notes", ""),
                "raw_headword": row.get("raw_headword", ""),
            }
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(output_rows[0]) if output_rows else []
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    summary = {
        "source": str(INPUT),
        "pending_count": len(rows),
        "category_counts": dict(category_counts),
        "flag_counts": dict(flag_counts),
        "meaning": {
            "pending_is_not_equal_to_wrong": True,
            "description": "pending表示尚未进入正式词库；列表中的记录可能是可修正的OCR词、释义噪声、切分疑点或需要人工确认的记录。",
        },
        "files": {"csv": str(OUTPUT), "markdown": str(SUMMARY_MD)},
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    with SUMMARY_MD.open("w", encoding="utf-8") as handle:
        handle.write("# TEM4 待审核词汇清单\n\n")
        handle.write(f"- 待审核总数：**{len(rows)}**\n")
        handle.write("- 说明：`pending` 只表示尚未进入正式词库，不代表每一条都一定错误。\n")
        handle.write("- 详细逐条清单：`tem4_pending_review_list.csv`，按原始页码和块号保留坐标。\n\n")
        handle.write("## 问题分类\n\n")
        handle.write("| 分类 | 数量 | 处理含义 |\n|---|---:|---|\n")
        descriptions = {
            "解析/边界疑点": "检查词头、释义是否错位，或是否把相邻行/例句粘在一起。",
            "词头或字母疑点": "检查俄文词形、е/ё、拉丁字母、数字及OCR相似字母。",
            "释义疑点": "检查中文释义缺失、过短、混入俄文例句或OCR乱码。",
            "低置信度": "自动识别信息不足，需结合原始扫描页确认。",
            "需人工确认": "未命中明显规则，但暂不自动放行。",
        }
        for category, count in category_counts.most_common():
            handle.write(f"| {category} | {count} | {descriptions.get(category, '')} |\n")
        handle.write("\n## 高频标记\n\n")
        for flag, count in flag_counts.most_common():
            handle.write(f"- {flag}：{count}\n")
        handle.write("\n## 前30条预览\n\n")
        handle.write("|序号|页/块|词头|当前释义|分类|主要原因|\n|---:|---|---|---|---|---|\n")
        for row in output_rows[:30]:
            meaning = row["meaning_zh"].replace("|", "／").replace("\n", " ")[:80]
            reason = row["issue_reason"].replace("|", "／")[:90]
            handle.write(
                f"|{row['pending_index']}|p{row['source_page']}/b{row['block_index']}|"
                f"{row['word']}|{meaning}|{row['issue_type']}|{reason}|\n"
            )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"csv={OUTPUT}")
    print(f"markdown={SUMMARY_MD}")


if __name__ == "__main__":
    main()
