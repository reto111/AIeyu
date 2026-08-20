from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
OUTPUT_DIR = ROOT / "data" / "processed" / "review_sheets"


FIELDS = [
    "segment_id",
    "audio_asset_id",
    "source_year",
    "audio_segment_order",
    "audio_segment_label",
    "file_name",
    "start_seconds",
    "end_seconds",
    "asr_text_ru",
    "corrected_text_ru",
    "text_zh",
    "review_status",
    "review_decision",
    "review_notes",
]


def export_review_sheet(year: int | None, asset_id: int | None, output: Path) -> dict[str, object]:
    query = """
        SELECT
          s.id AS segment_id,
          a.id AS audio_asset_id,
          a.source_year,
          a.segment_order AS audio_segment_order,
          a.segment_label AS audio_segment_label,
          a.file_name,
          s.start_seconds,
          s.end_seconds,
          s.text_ru AS asr_text_ru,
          s.text_zh,
          s.review_status
        FROM listening_segments s
        JOIN listening_assets a ON a.id = s.audio_asset_id
        WHERE 1 = 1
    """
    params: list[object] = []
    if year is not None:
        query += " AND a.source_year = ?"
        params.append(year)
    if asset_id is not None:
        query += " AND a.id = ?"
        params.append(asset_id)
    query += " ORDER BY a.source_year, a.segment_order, s.segment_order"

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            item = dict(row)
            item["corrected_text_ru"] = ""
            item["review_decision"] = ""
            item["review_notes"] = ""
            writer.writerow({field: item.get(field, "") for field in FIELDS})

    return {"output": str(output), "rows": len(rows), "year": year, "asset_id": asset_id}


def main() -> None:
    parser = argparse.ArgumentParser(description="Export listening ASR segments for human review.")
    parser.add_argument("--year", type=int)
    parser.add_argument("--asset-id", type=int)
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "tem8_listening_transcripts_review.csv",
    )
    args = parser.parse_args()

    result = export_review_sheet(args.year, args.asset_id, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
