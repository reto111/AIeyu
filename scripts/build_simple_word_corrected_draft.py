from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SIMPLE = ROOT / "data" / "processed" / "words" / "tem8_words_review_simple.csv"
DEFAULT_AUDIT = ROOT / "data" / "processed" / "words" / "tem8_words_simple_ocr_audit.csv"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "words" / "tem8_words_review_simple_corrected_draft.csv"
DEFAULT_REVIEW_ONLY = ROOT / "data" / "processed" / "words" / "tem8_words_simple_still_needs_review.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def audit_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (row.get("source_page", ""), row.get("block_index", ""), row.get("current_word", ""))


def simple_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (row.get("source_page", ""), row.get("block_index", ""), row.get("word", ""))


def append_note(notes: str, note: str) -> str:
    parts = [part for part in (notes or "").split(";") if part]
    if note not in parts:
        parts.append(note)
    return ";".join(parts)


def build_draft(simple_path: Path, audit_path: Path, output_path: Path, review_only_path: Path) -> dict[str, object]:
    simple_rows = read_csv(simple_path)
    audit_rows = read_csv(audit_path)
    audit_by_key = {audit_key(row): row for row in audit_rows}

    output_rows: list[dict[str, str]] = []
    review_rows: list[dict[str, str]] = []
    stats = {
        "kept_without_audit": 0,
        "suggested_corrections": 0,
        "high_confidence_corrections": 0,
        "medium_confidence_corrections": 0,
        "reject_or_split": 0,
        "needs_review": 0,
    }

    for row in simple_rows:
        out = dict(row)
        audit = audit_by_key.get(simple_key(row))
        if not audit:
            out["review_status"] = "pending"
            out["review_notes"] = append_note(out.get("review_notes", ""), "ocr_audit_no_shape_risk")
            stats["kept_without_audit"] += 1
        elif audit["action"] == "approve_correction":
            out["original_word"] = out.get("original_word") or out.get("word", "")
            out["word"] = audit["suggested_word"]
            out["review_status"] = "pending"
            out["review_notes"] = append_note(
                out.get("review_notes", ""),
                f"ocr_audit_suggested_{audit['confidence']}",
            )
            out["auto_notes"] = append_note(out.get("auto_notes", ""), audit.get("basis", "ocr_audit"))
            stats["suggested_corrections"] += 1
            if audit["confidence"] == "high":
                stats["high_confidence_corrections"] += 1
            elif audit["confidence"] == "medium":
                stats["medium_confidence_corrections"] += 1
        elif audit["action"] == "reject_or_split":
            out["review_status"] = "rejected_suggestion"
            out["review_notes"] = append_note(out.get("review_notes", ""), "ocr_audit_reject_or_split")
            out["manual_reason"] = append_note(out.get("manual_reason", ""), audit.get("basis", "ocr_audit_reject_or_split"))
            stats["reject_or_split"] += 1
            review_rows.append(out)
        else:
            out["review_status"] = "needs_review"
            out["review_notes"] = append_note(out.get("review_notes", ""), "ocr_audit_still_needs_review")
            out["manual_reason"] = append_note(out.get("manual_reason", ""), audit.get("reasons", "ocr_shape_risk"))
            stats["needs_review"] += 1
            review_rows.append(out)
        output_rows.append(out)

    fieldnames = list(simple_rows[0].keys()) if simple_rows else []
    write_csv(output_path, output_rows, fieldnames)
    write_csv(review_only_path, review_rows, fieldnames)
    stats["input_rows"] = len(simple_rows)
    stats["output_rows"] = len(output_rows)
    stats["review_only_rows"] = len(review_rows)
    stats["output"] = str(output_path)
    stats["review_only"] = str(review_only_path)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a corrected draft sheet from simple word OCR audit suggestions.")
    parser.add_argument("--simple", type=Path, default=DEFAULT_SIMPLE)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--review-only", type=Path, default=DEFAULT_REVIEW_ONLY)
    args = parser.parse_args()
    stats = build_draft(args.simple, args.audit, args.output, args.review_only)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
