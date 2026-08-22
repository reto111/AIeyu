from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SIMPLE = ROOT / "data" / "processed" / "words" / "tem8_words_review_simple.csv"
DEFAULT_CORRECTIONS = ROOT / "data" / "processed" / "words" / "tem8_words_local_correction_candidates.csv"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "words" / "tem8_words_approved_import.csv"

SOURCE_FILE = "tem8_russian_words.pdf"
IMPORT_CORRECTION_ACTIONS = {"approve_correction", "keep", "keep_optional"}
CYRILLIC_HEADWORD_RE = re.compile(r"^[А-Яа-яЁё-]+$")


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
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def is_importable_word(word: str) -> bool:
    word = normalize_text(word)
    return bool(word and CYRILLIC_HEADWORD_RE.match(word))


def approved_simple_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    approved: list[dict[str, str]] = []
    skipped = 0
    for row in rows:
        word = normalize_text(row.get("word", ""))
        meaning = normalize_text(row.get("meaning_zh", ""))
        if not is_importable_word(word) or not meaning:
            skipped += 1
            continue
        out = {name: row.get(name, "") for name in FIELDNAMES}
        out["word"] = word
        out["meaning_zh"] = meaning
        out["review_status"] = "approved"
        out["review_notes"] = normalize_text(out.get("review_notes", ""))
        approved.append(out)
    return approved, skipped


def approved_correction_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    approved: list[dict[str, str]] = []
    skipped = 0
    for row in rows:
        action = normalize_text(row.get("action", ""))
        if action not in IMPORT_CORRECTION_ACTIONS:
            skipped += 1
            continue
        word = normalize_text(row.get("suggested_word", ""))
        meaning = normalize_text(row.get("suggested_meaning_zh", ""))
        if not is_importable_word(word) or not meaning:
            skipped += 1
            continue
        raw_payload = {
            "current_word": row.get("current_word", ""),
            "original_word": row.get("original_word", ""),
            "action": action,
            "confidence": row.get("confidence", ""),
            "basis": row.get("basis", ""),
        }
        approved.append(
            {
                "source_file": SOURCE_FILE,
                "source_page": normalize_text(row.get("source_page", "")),
                "block_index": normalize_text(row.get("block_index", "")),
                "word": word,
                "original_word": normalize_text(row.get("original_word", "")),
                "lemma": "",
                "part_of_speech": "",
                "meaning_zh": meaning,
                "raw_meaning_zh": meaning,
                "auto_confidence": normalize_text(row.get("confidence", "")),
                "auto_notes": f"local_ai_correction;action={action}",
                "review_status": "approved",
                "review_notes": "user_approved_local_correction",
                "manual_reason": "",
                "raw_headword": normalize_text(row.get("current_word", "")),
                "raw_block": json.dumps(raw_payload, ensure_ascii=False),
            }
        )
    return approved, skipped


def dedupe_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    duplicates = 0
    for row in rows:
        key = (row["word"].lower(), normalize_text(row.get("part_of_speech", "")).lower())
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        deduped.append(row)
    return deduped, duplicates


def build_import_sheet(
    simple_path: Path,
    corrections_path: Path,
    output_path: Path,
    include_simple: bool = False,
) -> dict[str, int | str]:
    simple_rows = read_csv(simple_path) if include_simple else []
    correction_rows = read_csv(corrections_path)
    approved_simple, simple_skipped = approved_simple_rows(simple_rows)
    approved_corrections, correction_skipped = approved_correction_rows(correction_rows)
    merged, duplicates = dedupe_rows([*approved_simple, *approved_corrections])
    write_csv(output_path, merged)
    return {
        "simple_input_rows": len(simple_rows),
        "simple_approved_rows": len(approved_simple),
        "simple_skipped_rows": simple_skipped,
        "correction_input_rows": len(correction_rows),
        "correction_approved_rows": len(approved_corrections),
        "correction_skipped_rows": correction_skipped,
        "duplicate_rows_removed": duplicates,
        "output_rows": len(merged),
        "output": str(output_path),
        "include_simple": include_simple,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build approved vocabulary import CSV from reviewed word sheets.")
    parser.add_argument("--simple", type=Path, default=DEFAULT_SIMPLE)
    parser.add_argument("--corrections", type=Path, default=DEFAULT_CORRECTIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--include-simple",
        action="store_true",
        help="Also include rows from tem8_words_review_simple.csv after that sheet has been manually checked.",
    )
    args = parser.parse_args()
    stats = build_import_sheet(args.simple, args.corrections, args.output, include_simple=args.include_simple)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
