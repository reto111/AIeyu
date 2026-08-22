from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXISTING_APPROVED = ROOT / "data" / "processed" / "words" / "tem8_words_approved_import.csv"
DEFAULT_LLM_APPROVED = ROOT / "data" / "processed" / "words" / "tem8_words_llm_approved_only.csv"
DEFAULT_CLEAN_APPROVED = ROOT / "data" / "processed" / "words" / "tem8_words_not_checked_clean_candidates.csv"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "words" / "tem8_words_final_approved_for_import.csv"

VALID_HEADWORD_RE = re.compile(r"^[А-Яа-яЁё -]+$")

REJECT_HEADWORDS = {
    "кает",
    "пол-литрамолока",
    "ряются",
    "Поплатьювстречают",
}

WORD_CORRECTIONS = {
    "настрбенный": "настроенный",
    "нбвшество": "новшество",
    "парадбкс": "парадокс",
    "спосдбить": "приспособить",
}

MEANING_CORRECTIONS = {
    "абажур": "灯罩, 灯伞; 带灯罩的灯",
    "активизировать": "使积极起来; 使活跃起来",
    "библия": "圣经",
    "брить": "刮, 剃; 给某人剃头",
    "бюрократизм": "官僚主义",
    "вставлять": "插入, 嵌入; 装上, 镶上",
    "вплоть": "一直到; 甚至连某事也",
    "гарантировать": "保证; 对某事给予保证",
    "дуэль": "决斗; 要求与某人决斗",
    "забирать": "拿走, 取走; 抓走; 征召入伍",
    "кандидатура": "候选资格; 候选人选; 推举某人为候选人",
    "каторга": "苦役; 苦役流放",
    "Кыргызстан": "吉尔吉斯斯坦",
    "меч": "剑; 刀剑",
    "менять": "更换; 用某物交换",
    "накладывать": "把某物放在某物上; 缠上, 包扎; 涂上",
    "настроенный": "有某种心情的; 有兴致的, 乐意的; 调好的",
    "новатор": "创新者, 革新者",
    "новшество": "新事物, 新发明; 革新",
    "облетать": "绕飞; 飞遍; 飞过",
    "обусловливать": "以某事为条件; 决定, 制约",
    "ожидаться": "被预料, 预计将发生",
    "опережать": "超过, 赶在前面",
    "основываться": "以某事为根据; 基于",
    "охлаждение": "冷却; 变冷",
    "перебрасывать": "扔过; 扔到另一边; 架设; 调拨, 转移",
    "планировать": "计划, 拟定; 有计划地安排; 打算",
    "плавание": "游泳; 航行",
    "повисать": "挂在某物上; 垂下",
    "повреждать": "损坏; 弄伤; 使受损害",
    "подбегать": "跑到跟前; 跑近",
    "подвергать": "使遭受; 使经受",
    "предоставляться": "被提供, 被给予; 获得发言机会",
    "претендент": "觊觎者, 希望得到某物者; 竞争者",
    "прерывать": "中止, 打断; 使停顿",
    "привязывать": "把某物系在某物上; 使依附",
    "приспособить": "使适合于, 使适应于; 改成适宜于某用途",
    "прославиться": "出名, 驰名; 因某事而获得荣誉",
    "рваться": "撕裂; 猛冲; 极想去",
    "сволочь": "坏蛋, 恶棍, 流氓",
    "связываться": "联系, 联络; 同某人打交道",
    "сопровождаться": "伴随, 伴有; 与某事同时发生",
    "спасаться": "得救; 逃脱; 免受某种危险",
    "тактика": "战术; 策略",
    "таможня": "海关",
    "телохранитель": "侍卫, 卫士; 警卫员, 保镖",
    "теряться": "丢失, 消失; 张皇失措, 局促不安",
    "толковый": "明白道理的, 有理智的, 有见识的, 精明能干的; 有条理的; 有注释的",
    "торговаться": "讨价还价; 同某人讲价",
    "уводить": "领走, 带走; 带离",
    "характеризоваться": "以某事为特征; 具有某种特征",
    "чуждый": "别人的; 外来的, 异己的; 陌生的; 不具有某种感情的",
}

FIELDNAMES = [
    "source_file",
    "source_page",
    "block_index",
    "word",
    "original_word",
    "lemma",
    "part_of_speech",
    "meaning_zh",
    "raw_meaning_zh",
    "auto_confidence",
    "auto_notes",
    "review_status",
    "review_notes",
    "manual_reason",
    "raw_headword",
    "raw_block",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def normalize_row(row: dict[str, str], review_note: str) -> dict[str, str] | None:
    word = normalize(row.get("word", ""))
    meaning = normalize(row.get("meaning_zh", ""))
    if not word or not meaning:
        return None
    if word in REJECT_HEADWORDS:
        return None
    corrected_word = WORD_CORRECTIONS.get(word)
    if corrected_word:
        word = corrected_word
    if not VALID_HEADWORD_RE.match(word):
        return None
    out = {field: row.get(field, "") for field in FIELDNAMES}
    out["source_file"] = normalize(out.get("source_file", "")) or "tem8_russian_words.pdf"
    if corrected_word and not normalize(out.get("original_word", "")):
        out["original_word"] = normalize(row.get("word", ""))
    out["word"] = word
    out["meaning_zh"] = MEANING_CORRECTIONS.get(word, meaning)
    out["review_status"] = "approved"
    existing_notes = normalize(out.get("review_notes", ""))
    out["review_notes"] = ";".join(part for part in [existing_notes, review_note] if part)
    return out


def collect_rows(paths: list[tuple[Path, str]]) -> tuple[list[dict[str, str]], dict[str, int]]:
    collected: list[dict[str, str]] = []
    stats: dict[str, int] = {
        "input_rows": 0,
        "accepted_before_dedupe": 0,
        "invalid_rows": 0,
        "duplicates_removed": 0,
    }
    for path, note in paths:
        rows = read_csv(path)
        stats[f"input_{path.name}"] = len(rows)
        stats["input_rows"] += len(rows)
        for row in rows:
            normalized = normalize_row(row, note)
            if normalized is None:
                stats["invalid_rows"] += 1
                continue
            collected.append(normalized)
            stats["accepted_before_dedupe"] += 1

    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in collected:
        key = (row["word"].casefold(), normalize(row.get("part_of_speech", "")).casefold())
        if key in seen:
            stats["duplicates_removed"] += 1
            continue
        seen.add(key)
        deduped.append(row)
    return deduped, stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Build final approved vocabulary import CSV from reviewed safe sources.")
    parser.add_argument("--existing-approved", type=Path, default=DEFAULT_EXISTING_APPROVED)
    parser.add_argument("--llm-approved", type=Path, default=DEFAULT_LLM_APPROVED)
    parser.add_argument("--clean-approved", type=Path, default=DEFAULT_CLEAN_APPROVED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rows, stats = collect_rows(
        [
            (args.existing_approved, "user_approved_local_corrections"),
            (args.llm_approved, "user_allowed_llm_approved_corrections"),
            (args.clean_approved, "user_confirmed_clean_candidate_sample"),
        ]
    )
    write_csv(args.output, rows)
    stats["output_rows"] = len(rows)
    stats["output"] = str(args.output)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
