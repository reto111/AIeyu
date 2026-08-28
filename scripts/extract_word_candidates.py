from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OCR_DIR = ROOT / "data" / "processed" / "words" / "ocr_text" / "pages"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "words" / "tem8_words_candidates.csv"
DEFAULT_REVIEW_OUTPUT = ROOT / "data" / "processed" / "words" / "tem8_words_review.csv"

CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
LATIN_RE = re.compile(r"[A-Za-z]")
PAGE_FILE_RE = re.compile(r"page_(\d{3})\.txt$")

NOISE_PREFIXES = (
    "参考书目",
    "词汇篇",
    "外语教学",
    "高等学校",
    "本书特点",
)

ENTRY_START_RE = re.compile(
    r"^\s*[#№\|\.\-`'\"“”‘’·*]*\s*[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё0-9ЪъЬь\-]{1,}"
    r"\s*(?:[,‚，]|-[A-Za-zА-Яа-яЁё0-9]|—)"
)


def page_no_from_path(path: Path) -> int:
    match = PAGE_FILE_RE.search(path.name)
    if not match:
        raise ValueError(f"Cannot read page number from {path.name}")
    return int(match.group(1))


def split_blocks(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    rough_blocks = re.split(r"\n\s*\n+", normalized)
    blocks: list[str] = []
    for rough in rough_blocks:
        current: list[str] = []
        for raw_line in rough.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if current and looks_like_entry_start(line):
                blocks.append("\n".join(current).strip())
                current = [line]
            else:
                current.append(line)
        if current:
            blocks.append("\n".join(current).strip())
    return [block.strip() for block in blocks if block.strip()]


def looks_like_entry_start(line: str) -> bool:
    if not ENTRY_START_RE.search(line):
        return False
    if not (CYRILLIC_RE.search(line) or CHINESE_RE.search(line)):
        return False
    return True


def is_candidate_block(block: str) -> bool:
    compact = block.strip()
    if len(compact) < 8:
        return False
    first = compact.splitlines()[0].strip()
    if any(first.startswith(prefix) for prefix in NOISE_PREFIXES):
        return False
    return bool(CYRILLIC_RE.search(compact) and CHINESE_RE.search(compact))


def clean_headword(raw: str) -> str:
    head = raw.strip()
    head = re.sub(r"^[#№\|\.\s、`'\"“”‘’·*]+", "", head)
    head = re.split(r"[\[【(（:：;；]", head, maxsplit=1)[0].strip()
    head = re.split(r"\s{2,}", head, maxsplit=1)[0].strip()
    if "," in head:
        head = head.split(",", 1)[0].strip()
    if "‚" in head:
        head = head.split("‚", 1)[0].strip()
    head = re.split(r"\s+-[A-Za-zА-Яа-яЁё0-9]", head, maxsplit=1)[0].strip()
    head = re.sub(r"\s+", " ", head)
    return head[:80]


def extract_headword(block: str) -> tuple[str, str, str]:
    first_line = block.splitlines()[0].strip()
    raw_head = first_line
    word = clean_headword(raw_head)
    parse_status = "parsed"
    notes: list[str] = []
    if not CYRILLIC_RE.search(word):
        parse_status = "needs_review"
        notes.append("headword_has_no_cyrillic")
    if any(char.isdigit() for char in word):
        parse_status = "needs_review"
        notes.append("headword_has_digit")
    if LATIN_RE.search(word):
        parse_status = "needs_review"
        notes.append("headword_has_latin")
    if len(word) <= 1:
        parse_status = "needs_review"
        notes.append("headword_too_short")
    return word, parse_status, ";".join(notes)


def first_part_of_speech(block: str) -> str:
    match = re.search(r"[\[【]\s*([^\]】]{1,12})\s*[\]】]", block)
    return match.group(1).strip() if match else ""


def first_meaning_zh(block: str) -> str:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    text = " ".join(lines)
    match = CHINESE_RE.search(text)
    if not match:
        return ""
    meaning = text[match.start() :]
    meaning = re.sub(r"^[^\]】]{1,20}[\]】]\s*", "", meaning)
    meaning = re.sub(r"\s+", " ", meaning)
    return meaning[:500]


def iter_candidates(ocr_dir: Path, prefix: str, source_file: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(ocr_dir.glob(f"{prefix}_page_*.txt")):
        page_no = int(path.stem.rsplit("_", 1)[-1])
        text = path.read_text(encoding="utf-8", errors="replace")
        for block_index, block in enumerate(split_blocks(text), start=1):
            if not is_candidate_block(block):
                continue
            word, parse_status, notes = extract_headword(block)
            if not word:
                continue
            rows.append(
                {
                    "source_file": source_file,
                    "source_page": str(page_no),
                    "block_index": str(block_index),
                    "raw_headword": block.splitlines()[0].strip()[:160],
                    "word": word,
                    "lemma": "",
                    "part_of_speech": first_part_of_speech(block),
                    "meaning_zh": first_meaning_zh(block),
                    "raw_block": block,
                    "parse_status": parse_status,
                    "review_status": "pending",
                    "review_notes": notes,
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_file",
        "source_page",
        "block_index",
        "raw_headword",
        "word",
        "lemma",
        "part_of_speech",
        "meaning_zh",
        "raw_block",
        "parse_status",
        "review_status",
        "review_notes",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract reviewable word candidates from OCR text.")
    parser.add_argument("--ocr-dir", type=Path, default=DEFAULT_OCR_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--review-output", type=Path, default=DEFAULT_REVIEW_OUTPUT)
    parser.add_argument("--prefix", default="tem8_russian_words")
    parser.add_argument("--source-file", default="tem8_russian_words.pdf")
    args = parser.parse_args()

    rows = iter_candidates(args.ocr_dir, args.prefix, args.source_file)
    write_csv(args.output, rows)
    write_csv(args.review_output, rows)

    parsed = sum(1 for row in rows if row["parse_status"] == "parsed")
    needs_review = len(rows) - parsed
    print(
        {
            "candidates": len(rows),
            "parsed": parsed,
            "needs_review": needs_review,
            "output": str(args.output),
            "review_output": str(args.review_output),
        }
    )


if __name__ == "__main__":
    main()
