from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
DEFAULT_REVIEW_CSV = ROOT / "data" / "processed" / "review_sheets" / "tem8_listening_transcripts_review.csv"


APPROVE_VALUES = {"approved", "reviewed", "human_verified"}


def apply_review(path: Path, dry_run: bool) -> dict[str, object]:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig", newline="")))
    reviewed_assets: set[int] = set()
    updated_segments = 0
    skipped_rows = 0

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for row in rows:
            decision = (row.get("review_decision") or "").strip().lower()
            corrected = (row.get("corrected_text_ru") or "").strip()
            segment_id_raw = (row.get("segment_id") or "").strip()
            asset_id_raw = (row.get("audio_asset_id") or "").strip()

            if not segment_id_raw or not asset_id_raw:
                skipped_rows += 1
                continue
            if decision not in APPROVE_VALUES or not corrected:
                skipped_rows += 1
                continue

            segment_id = int(segment_id_raw)
            asset_id = int(asset_id_raw)
            reviewed_assets.add(asset_id)
            updated_segments += 1

            if dry_run:
                continue

            conn.execute(
                """
                UPDATE listening_segments
                SET text_ru = ?,
                    text_zh = COALESCE(NULLIF(?, ''), text_zh),
                    review_status = 'reviewed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (corrected, (row.get("text_zh") or "").strip(), segment_id),
            )

        if not dry_run:
            for asset_id in reviewed_assets:
                all_count = conn.execute(
                    "SELECT COUNT(*) FROM listening_segments WHERE audio_asset_id = ?",
                    (asset_id,),
                ).fetchone()[0]
                reviewed_count = conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM listening_segments
                    WHERE audio_asset_id = ? AND review_status = 'reviewed'
                    """,
                    (asset_id,),
                ).fetchone()[0]
                if all_count and all_count == reviewed_count:
                    text = "\n".join(
                        row[0]
                        for row in conn.execute(
                            """
                            SELECT text_ru
                            FROM listening_segments
                            WHERE audio_asset_id = ?
                            ORDER BY segment_order
                            """,
                            (asset_id,),
                        ).fetchall()
                    ).strip()
                    conn.execute(
                        """
                        INSERT INTO listening_transcripts (
                          audio_asset_id, transcript_type, provider, model_name,
                          language, transcript_text
                        )
                        VALUES (?, 'human_corrected', 'manual_review', 'human', 'ru', ?)
                        """,
                        (asset_id, text),
                    )
                    conn.execute(
                        """
                        UPDATE listening_assets
                        SET asr_status = 'human_verified',
                            transcript_status = 'human_verified',
                            review_status = 'reviewed',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (asset_id,),
                    )
            conn.commit()

    return {
        "status": "dry_run" if dry_run else "ok",
        "review_file": str(path),
        "updated_segments": updated_segments,
        "skipped_rows": skipped_rows,
        "reviewed_assets_touched": sorted(reviewed_assets),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply reviewed listening transcript corrections.")
    parser.add_argument("--input", type=Path, default=DEFAULT_REVIEW_CSV)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = apply_review(args.input, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
