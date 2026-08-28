from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "processed" / "words" / "tem8_words_review.csv"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "words" / "tem8_words_review_cleaned.csv"
DEFAULT_REMOVED = ROOT / "data" / "processed" / "words" / "tem8_words_removed_nonwords.csv"

CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
ONLY_CYRILLIC_WORD_RE = re.compile(r"^[А-Яа-яЁё][А-Яа-яЁё-]{1,}$")
SINGLE_CYRILLIC_WORD_RE = re.compile(r"^[А-Яа-яЁё]$")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
LATIN_RE = re.compile(r"[A-Za-z]")

LATIN_TO_CYRILLIC = str.maketrans(
    {
        "A": "а",
        "B": "в",
        "C": "с",
        "D": "д",
        "E": "е",
        "F": "ф",
        "G": "г",
        "H": "н",
        "I": "и",
        "K": "к",
        "L": "л",
        "M": "м",
        "N": "н",
        "O": "о",
        "P": "р",
        "R": "р",
        "S": "с",
        "T": "т",
        "U": "и",
        "V": "у",
        "X": "х",
        "Y": "у",
        "Z": "з",
        "a": "а",
        "b": "ь",
        "c": "с",
        "d": "д",
        "e": "е",
        "f": "ф",
        "g": "г",
        "h": "н",
        "i": "и",
        "j": "й",
        "k": "к",
        "l": "л",
        "m": "м",
        "n": "н",
        "o": "о",
        "p": "р",
        "q": "я",
        "s": "с",
        "t": "т",
        "u": "и",
        "v": "у",
        "w": "ш",
        "x": "х",
        "y": "у",
        "z": "з",
        "r": "г",
        "3": "з",
        "6": "б",
        "0": "о",
    }
)

NOISE_WORDS = {
    "ан",
    "isbn",
    "cip",
    "email",
    # Inflection labels that OCR may mistake for a headword.
    "кого-что",
    "кем-чем",
    "кого-чего",
    "го-что",
    "го-чего",
    "кому-чему",
    "чего-что",
}

NONWORD_HEADINGS = (
    "高 等 学 校",
    "图 书",
    "在 本 书",
    "参考书目",
    "词 汇 篇",
    "八 级 词 汇",
)


def clean_spaces(text: str) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"\s+([,，.。:：;；/）)])", r"\1", text)
    text = re.sub(r"([(（])\s+", r"\1", text)
    return text.strip()


def strip_headword_noise(word: str) -> str:
    word = (word or "").strip()
    word = re.sub(r"^[#№\|\.\s、`'\"“”‘’·*]+", "", word)
    word = re.split(r"[\[【(（:：;；]", word, maxsplit=1)[0].strip()
    if "," in word:
        word = word.split(",", 1)[0].strip()
    if "‚" in word:
        word = word.split("‚", 1)[0].strip()
    word = re.split(r"\s+-[A-Za-zА-Яа-яЁё0-9]", word, maxsplit=1)[0].strip()
    word = re.split(r"\s+\d", word, maxsplit=1)[0].strip()
    word = re.sub(r"\s+", " ", word)
    word = re.sub(r"[^A-Za-zА-Яа-яЁё0-9-]", "", word)
    return word


def transliterate_ocr_word(word: str) -> str:
    converted = strip_headword_noise(word).translate(LATIN_TO_CYRILLIC)
    converted = re.sub(r"[^А-Яа-яЁё-]", "", converted)
    return converted


def first_cyrillic_token(text: str) -> str:
    for token in re.findall(r"[А-Яа-яЁё][А-Яа-яЁё-]{2,}", text or ""):
        token_lower = token.lower()
        if token_lower not in NOISE_WORDS:
            return token
    return ""


def clean_meaning(text: str) -> str:
    text = clean_spaces(text)
    text = re.sub(r"^[^\]】]{1,20}[\]】]\s*", "", text)
    text = re.sub(r"^[#@&№ЖНЙТЛ\s,，:：;；.-]+", "", text)
    return clean_spaces(text)


def has_useful_meaning(text: str) -> bool:
    return bool(CHINESE_RE.search(text or ""))


def suggest_word(row: dict[str, str]) -> tuple[str, str, str]:
    original = strip_headword_noise(row.get("word", ""))
    raw_block = row.get("raw_block", "")
    notes: list[str] = []
    if len(original) == 1:
        single = original.translate(LATIN_TO_CYRILLIC)
        single = re.sub(r"[^А-Яа-яЁё]", "", single).lower()
        if SINGLE_CYRILLIC_WORD_RE.match(single):
            return single, "low", "single_letter_function_word_candidate"
    if ONLY_CYRILLIC_WORD_RE.match(original):
        return original, "high", "kept_cyrillic_headword"
    if CYRILLIC_RE.search(original) and not LATIN_RE.search(original):
        cyrillic_clean = re.sub(r"[^А-Яа-яЁё-]", "", original)
        if ONLY_CYRILLIC_WORD_RE.match(cyrillic_clean):
            return cyrillic_clean, "high", "removed_ocr_tail_from_cyrillic_headword"

    transliterated = transliterate_ocr_word(original)
    if ONLY_CYRILLIC_WORD_RE.match(transliterated):
        notes.append("latin_digit_ocr_transliterated")
        if LATIN_RE.search(original) or any(char.isdigit() for char in original):
            return transliterated, "medium", ";".join(notes)

    token = first_cyrillic_token(raw_block)
    if token:
        notes.append("fallback_first_cyrillic_token")
        return token, "low", ";".join(notes)

    return original, "reject", "no_plausible_cyrillic_word"


def should_remove(row: dict[str, str], suggested_word: str, meaning: str, confidence: str) -> tuple[bool, str]:
    page = int(row.get("source_page") or 0)
    raw_headword = row.get("raw_headword", "")
    raw_block = row.get("raw_block", "")
    if page < 7:
        return True, "front_matter"
    if any(raw_headword.startswith(prefix) or raw_block.startswith(prefix) for prefix in NONWORD_HEADINGS):
        return True, "heading_or_book_matter"
    if confidence == "reject":
        return True, "no_plausible_word"
    if len(suggested_word) <= 1 and "八级词汇" in meaning:
        return True, "single_letter_heading"
    if suggested_word.lower() in NOISE_WORDS:
        return True, "noise_token"
    return False, ""


def clean_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    kept: list[dict[str, str]] = []
    removed: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        suggested_word, confidence, auto_notes = suggest_word(row)
        meaning = clean_meaning(row.get("meaning_zh", ""))
        remove, remove_reason = should_remove(row, suggested_word, meaning, confidence)
        cleaned = dict(row)
        cleaned["original_word"] = row.get("word", "")
        cleaned["word"] = suggested_word
        cleaned["meaning_zh"] = meaning
        cleaned["auto_confidence"] = confidence
        if not has_useful_meaning(meaning):
            auto_notes = f"{auto_notes};missing_chinese_meaning" if auto_notes else "missing_chinese_meaning"
            if confidence == "high":
                cleaned["auto_confidence"] = "low"
        cleaned["auto_notes"] = auto_notes
        cleaned["review_status"] = "pending"
        cleaned["review_notes"] = row.get("review_notes", "")
        if remove:
            cleaned["remove_reason"] = remove_reason
            removed.append(cleaned)
            continue
        key = (suggested_word.lower(), row.get("part_of_speech", "").strip(), meaning[:80])
        if key in seen:
            cleaned["remove_reason"] = "duplicate_candidate"
            removed.append(cleaned)
            continue
        seen.add(key)
        kept.append(cleaned)
    return kept, removed


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean OCR vocabulary review sheet.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--removed", type=Path, default=DEFAULT_REMOVED)
    args = parser.parse_args()

    rows = read_csv(args.input)
    kept, removed = clean_rows(rows)
    fieldnames = [
        "source_file",
        "source_page",
        "block_index",
        "word",
        "original_word",
        "lemma",
        "part_of_speech",
        "meaning_zh",
        "auto_confidence",
        "auto_notes",
        "parse_status",
        "review_status",
        "review_notes",
        "raw_headword",
        "raw_block",
    ]
    removed_fieldnames = [*fieldnames, "remove_reason"]
    write_csv(args.output, kept, fieldnames)
    write_csv(args.removed, removed, removed_fieldnames)

    confidence_counts: dict[str, int] = {}
    for row in kept:
        confidence_counts[row["auto_confidence"]] = confidence_counts.get(row["auto_confidence"], 0) + 1
    print(
        {
            "input_rows": len(rows),
            "kept_rows": len(kept),
            "removed_rows": len(removed),
            "confidence": confidence_counts,
            "output": str(args.output),
            "removed": str(args.removed),
        }
    )


if __name__ == "__main__":
    main()
