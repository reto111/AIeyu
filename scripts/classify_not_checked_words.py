from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "processed" / "words" / "tem8_words_llm_corrected_candidates.csv"
DEFAULT_DB = ROOT / "database" / "russian_ai_tutor.sqlite"
DEFAULT_CLEAN = ROOT / "data" / "processed" / "words" / "tem8_words_not_checked_clean_candidates.csv"
DEFAULT_NEEDS_LLM = ROOT / "data" / "processed" / "words" / "tem8_words_not_checked_needs_llm_review.csv"
DEFAULT_REJECT = ROOT / "data" / "processed" / "words" / "tem8_words_not_checked_reject_candidates.csv"
DEFAULT_SUMMARY = ROOT / "data" / "processed" / "words" / "tem8_words_not_checked_classification_summary.json"

CYRILLIC_SINGLE_WORD_RE = re.compile(r"^[А-Яа-яЁё-]{2,32}$")
CYRILLIC_SPACE_WORD_RE = re.compile(r"^[А-Яа-яЁё -]{2,48}$")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
BAD_HEADWORD_RE = re.compile(r"[A-Za-z0-9@#№&=+<>/\\|{}\[\]【】（）()]")
VOWEL_RE = re.compile(r"[аеёиоуыэюяАЕЁИОУЫЭЮЯ]")
CASE_FRAGMENT_RE = re.compile(r"(^|[-\s])(кого|кого-что|кем|кем-чем|чего|чему|что|чем|то-что|го-что)([-\s]|$)", re.IGNORECASE)
VERY_LONG_CONSONANT_CLUSTER_RE = re.compile(r"[бвгджзклмнпрстфхцчшщ]{7,}", re.IGNORECASE)
RAW_SENTENCE_RE = re.compile(r"[.!?。！？].{0,40}[\u4e00-\u9fff]")

NOISE_CHARS = set(
    "恩鹏阮咤蝉憎魍疆啬踉冤怦怯愫悯慊氓疃邋翼崛"
    "鹰喱嘲阴倩纱夺茬炕屏酰囱趸蓁铬阔薄滢乩瑁"
)
REAL_YO_ROOTS = (
    "актёр",
    "берёз",
    "водоём",
    "дирижёр",
    "жёлт",
    "жёст",
    "зелён",
    "лёгк",
    "решёт",
    "свёкл",
    "трёх",
    "чёрн",
    "ягнён",
)
SUSPICIOUS_OCR_WORD_RE = re.compile(
    r"(бнн|бльн|бтств|брств|брник|бк$|блк|бвк|бдств|бс$|бО|Оо|оО|дн$|днн|рдн|пб|сбв|тбв|цбв|льбн|крбд|блог$)",
    re.IGNORECASE,
)
KNOWN_SUSPICIOUS_WORDS = {
    "бактёрия",
    "банкродство",
    "батальбн",
    "белбк",
    "беспризбрник",
    "библог",
    "бандербль",
    "горшобк",
    "госпбодствовать",
    "дореволюцибнный",
    "пурачбк",
    "загазбованный",
    "заготбвка",
    "заинтересбванный",
    "заинтересбвывать",
    "заинтересбовываться",
    "инвестицибнный",
    "инновациднный",
    "информацибнный",
    "ирдния",
    "кипятбк",
    "колбнна",
    "кбнсул",
    "лаборатбрия",
    "молбоденький",
    "молотбк",
    "монопблия",
    "микрорайдн",
}
PHRASE_HINTS = (
    "谚",
    "格支配",
    "例句",
    "文章的标题",
    "莫斯科不是",
    "星星之火",
    "需求与供应",
    "民族解放运动",
)


EXTRA_FIELDS = [
    "not_checked_bucket",
    "not_checked_reasons",
    "not_checked_notes",
]


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_existing_words(db_path: Path) -> set[str]:
    if not db_path.exists():
        return set()
    conn = sqlite3.connect(db_path)
    try:
        return {
            normalize(row[0]).casefold()
            for row in conn.execute("select word from vocabulary_items")
            if row[0]
        }
    finally:
        conn.close()


def row_word(row: dict[str, str]) -> str:
    return normalize(row.get("word", ""))


def has_noise_meaning(meaning: str) -> bool:
    if any(char in meaning for char in NOISE_CHARS):
        return True
    if meaning.count("；") >= 4:
        return True
    if len(meaning) > 90 and any(mark in meaning for mark in "()/（）"):
        return True
    return False


def reject_reasons(row: dict[str, str], word: str, meaning: str) -> list[str]:
    raw = normalize(row.get("raw_block", ""))
    reasons: list[str] = []
    if not word:
        reasons.append("empty_word")
    if BAD_HEADWORD_RE.search(word):
        reasons.append("bad_headword_characters")
    if CASE_FRAGMENT_RE.search(word):
        reasons.append("case_government_fragment")
    if not CHINESE_RE.search(meaning):
        reasons.append("missing_chinese_meaning")
    if len(word) > 48:
        reasons.append("very_long_headword")
    if word.count("-") >= 3:
        reasons.append("too_many_hyphen_parts")
    if any(hint in meaning for hint in PHRASE_HINTS):
        reasons.append("phrase_or_sentence_meaning_hint")
    if RAW_SENTENCE_RE.search(raw) and len(word) > 18:
        reasons.append("raw_sentence_fragment")
    return reasons


def needs_llm_reasons(row: dict[str, str], word: str, meaning: str) -> list[str]:
    notes = normalize(row.get("review_notes", ""))
    auto_notes = normalize(row.get("auto_notes", ""))
    reasons: list[str] = []
    if not CYRILLIC_SPACE_WORD_RE.match(word):
        reasons.append("nonstandard_cyrillic_shape")
    if " " in word:
        reasons.append("multi_word_headword")
    if not VOWEL_RE.search(word):
        reasons.append("no_vowel")
    if VERY_LONG_CONSONANT_CLUSTER_RE.search(word):
        reasons.append("long_consonant_cluster")
    if len(word) > 28:
        reasons.append("long_headword")
    if has_noise_meaning(meaning):
        reasons.append("noisy_or_long_meaning")
    lower_word = word.lower()
    if "ё" in lower_word and not any(lower_word.startswith(root) for root in REAL_YO_ROOTS):
        reasons.append("yo_e_or_stress_uncertain")
    if lower_word in KNOWN_SUSPICIOUS_WORDS or SUSPICIOUS_OCR_WORD_RE.search(word):
        reasons.append("suspicious_o_b_ocr_pattern")
    if "headword_has_digit" in notes or "headword_has_latin" in notes:
        reasons.append("previous_digit_or_latin_note")
    if "yo_e_uncertain" in auto_notes or "manual" in normalize(row.get("manual_reason", "")):
        reasons.append("previous_manual_uncertainty")
    return reasons


def classify_rows(rows: list[dict[str, str]], existing_words: set[str]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    clean: list[dict[str, str]] = []
    needs_llm: list[dict[str, str]] = []
    reject: list[dict[str, str]] = []
    seen: set[str] = set(existing_words)

    for row in rows:
        if row.get("llm_review_status") != "not_checked":
            continue
        word = row_word(row)
        meaning = normalize(row.get("meaning_zh", ""))
        key = word.casefold()
        out = dict(row)

        hard_reasons = reject_reasons(row, word, meaning)
        soft_reasons = needs_llm_reasons(row, word, meaning)

        if key in seen:
            hard_reasons.append("duplicate_with_existing_or_prior_candidate")

        if hard_reasons:
            out["not_checked_bucket"] = "reject_candidate"
            out["not_checked_reasons"] = ";".join(hard_reasons)
            out["not_checked_notes"] = "Do not import unless manually recovered from source PDF."
            reject.append(out)
            continue

        if soft_reasons:
            out["not_checked_bucket"] = "needs_llm_review"
            out["not_checked_reasons"] = ";".join(soft_reasons)
            out["not_checked_notes"] = "Needs LLM/manual confirmation before use."
            needs_llm.append(out)
            seen.add(key)
            continue

        out["not_checked_bucket"] = "clean_candidate"
        out["not_checked_reasons"] = "clean_shape_core_meaning_present"
        out["not_checked_notes"] = "Machine-clean candidate; still requires sampling approval before import."
        clean.append(out)
        seen.add(key)

    return clean, needs_llm, reject


def summarize(clean: list[dict[str, str]], needs_llm: list[dict[str, str]], reject: list[dict[str, str]]) -> dict[str, object]:
    def reason_counts(rows: list[dict[str, str]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            for reason in row.get("not_checked_reasons", "").split(";"):
                if reason:
                    counts[reason] = counts.get(reason, 0) + 1
        return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

    return {
        "clean_candidates": len(clean),
        "needs_llm_review": len(needs_llm),
        "reject_candidates": len(reject),
        "total_classified": len(clean) + len(needs_llm) + len(reject),
        "needs_llm_reasons": reason_counts(needs_llm),
        "reject_reasons": reason_counts(reject),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify not_checked vocabulary rows into clean, LLM review, and reject buckets.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--clean", type=Path, default=DEFAULT_CLEAN)
    parser.add_argument("--needs-llm", type=Path, default=DEFAULT_NEEDS_LLM)
    parser.add_argument("--reject", type=Path, default=DEFAULT_REJECT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()

    rows = read_csv(args.input)
    existing_words = load_existing_words(args.db)
    clean, needs_llm, reject = classify_rows(rows, existing_words)
    fieldnames = [*rows[0].keys(), *EXTRA_FIELDS] if rows else EXTRA_FIELDS
    write_csv(args.clean, clean, fieldnames)
    write_csv(args.needs_llm, needs_llm, fieldnames)
    write_csv(args.reject, reject, fieldnames)
    summary = summarize(clean, needs_llm, reject)
    summary.update(
        {
            "input": str(args.input),
            "clean": str(args.clean),
            "needs_llm": str(args.needs_llm),
            "reject": str(args.reject),
            "summary": str(args.summary),
        }
    )
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
