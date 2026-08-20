from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
DEFAULT_AUDIO_ROOT = ROOT / "data" / "listening" / "raw_audio" / "tem8"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def natural_key(path: Path) -> list[int | str]:
    parts = re.split(r"(\d+)", path.stem)
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def infer_year(path: Path, audio_root: Path) -> int | None:
    relative_parts = path.relative_to(audio_root).parts
    for part in relative_parts:
        match = re.fullmatch(r"(20\d{2})", part)
        if match:
            return int(match.group(1))
    match = re.search(r"(20\d{2})", path.stem)
    return int(match.group(1)) if match else None


def infer_scope(path: Path, audio_root: Path) -> str:
    relative = path.relative_to(audio_root)
    return "full_exam" if len(relative.parts) == 1 else "segment"


def get_exam_ids(conn: sqlite3.Connection) -> tuple[int, int]:
    row = conn.execute(
        """
        SELECT es.id, el.id
        FROM exam_systems es
        JOIN exam_levels el ON el.exam_system_id = es.id
        WHERE es.code = 'TEM8_RU' AND el.code = 'TEM8'
        """
    ).fetchone()
    if row is None:
        raise ValueError("Missing TEM8_RU/TEM8. Initialize the database first.")
    return int(row[0]), int(row[1])


def scan_audio(audio_root: Path) -> list[Path]:
    return sorted(
        [path for path in audio_root.rglob("*") if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS],
        key=lambda item: (infer_year(item, audio_root) or 0, infer_scope(item, audio_root), natural_key(item)),
    )


def segment_order(path: Path, audio_root: Path, grouped: dict[int | None, list[Path]]) -> int:
    year = infer_year(path, audio_root)
    scope = infer_scope(path, audio_root)
    if scope == "full_exam":
        return 1
    siblings = sorted(grouped[year], key=natural_key)
    return siblings.index(path) + 1


def register(audio_root: Path, dry_run: bool) -> dict[str, object]:
    audio_root = audio_root.resolve()
    files = scan_audio(audio_root)
    grouped: dict[int | None, list[Path]] = {}
    for path in files:
        grouped.setdefault(infer_year(path, audio_root), []).append(path)

    registered: list[dict[str, object]] = []
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        exam_system_id, level_id = get_exam_ids(conn)

        for path in files:
            year = infer_year(path, audio_root)
            scope = infer_scope(path, audio_root)
            order = segment_order(path, audio_root, grouped)
            relative_path = path.relative_to(ROOT).as_posix()
            label = f"{year} 年俄语专八听力音频" if year else "俄语专八听力音频"
            segment_label = "整套音频" if scope == "full_exam" else f"分段 {order}"
            title = f"{label} - {segment_label}"
            item = {
                "source_year": year,
                "title": title,
                "file_path": relative_path,
                "file_name": path.name,
                "file_hash": sha256_file(path),
                "file_format": path.suffix.lower().lstrip("."),
                "file_size_bytes": path.stat().st_size,
                "asset_scope": scope,
                "segment_order": order,
                "segment_label": segment_label,
                "source_label": label,
            }
            registered.append(item)

            if dry_run:
                continue

            conn.execute(
                """
                INSERT INTO listening_assets (
                  exam_system_id, level_id, source_year, title, file_path, file_name,
                  file_hash, file_format, file_size_bytes, asset_scope, segment_order,
                  segment_label, source_label, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(exam_system_id, file_path) DO UPDATE SET
                  source_year = excluded.source_year,
                  title = excluded.title,
                  file_name = excluded.file_name,
                  file_hash = excluded.file_hash,
                  file_format = excluded.file_format,
                  file_size_bytes = excluded.file_size_bytes,
                  asset_scope = excluded.asset_scope,
                  segment_order = excluded.segment_order,
                  segment_label = excluded.segment_label,
                  source_label = excluded.source_label,
                  updated_at = CURRENT_TIMESTAMP
                """,
                (
                    exam_system_id,
                    level_id,
                    item["source_year"],
                    item["title"],
                    item["file_path"],
                    item["file_name"],
                    item["file_hash"],
                    item["file_format"],
                    item["file_size_bytes"],
                    item["asset_scope"],
                    item["segment_order"],
                    item["segment_label"],
                    item["source_label"],
                ),
            )
        if not dry_run:
            conn.commit()

    by_year: dict[str, int] = {}
    for item in registered:
        key = str(item["source_year"] or "unknown")
        by_year[key] = by_year.get(key, 0) + 1

    return {
        "status": "dry_run" if dry_run else "ok",
        "audio_root": str(audio_root),
        "file_count": len(registered),
        "by_year": by_year,
        "items": registered,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Register TEM8 listening audio assets.")
    parser.add_argument("--audio-root", default=str(DEFAULT_AUDIO_ROOT), help="Root folder containing TEM8 audio files.")
    parser.add_argument("--dry-run", action="store_true", help="Scan files without writing to the database.")
    args = parser.parse_args()

    result = register(Path(args.audio_root), dry_run=args.dry_run)
    printable = {key: value for key, value in result.items() if key != "items"}
    print(json.dumps(printable, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
