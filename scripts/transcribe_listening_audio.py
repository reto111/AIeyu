from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
OUTPUT_DIR = ROOT / "data" / "processed" / "listening_asr"


def require_faster_whisper():
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SystemExit(
            "Missing faster-whisper. Install it with: "
            r".venv\Scripts\python.exe -m pip install -r requirements-asr.txt"
        ) from exc
    return WhisperModel


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def find_asset(
    conn: sqlite3.Connection,
    asset_id: int | None,
    year: int | None,
    segment_order: int | None,
) -> sqlite3.Row:
    if asset_id is not None:
        row = conn.execute("SELECT * FROM listening_assets WHERE id = ?", (asset_id,)).fetchone()
        if row is None:
            raise SystemExit(f"Listening asset not found: {asset_id}")
        return row

    if year is None:
        raise SystemExit("Provide --asset-id, or provide --year with optional --segment-order.")

    if segment_order is None:
        rows = conn.execute(
            """
            SELECT *
            FROM listening_assets
            WHERE source_year = ?
            ORDER BY asset_scope, segment_order, file_name
            """,
            (year,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT *
            FROM listening_assets
            WHERE source_year = ? AND segment_order = ?
            ORDER BY asset_scope, file_name
            """,
            (year, segment_order),
        ).fetchall()

    if not rows:
        raise SystemExit(f"No listening asset found for year={year}, segment_order={segment_order}.")
    if len(rows) > 1:
        choices = [f"id={row['id']} {row['file_path']}" for row in rows]
        raise SystemExit("Multiple assets matched. Use --asset-id:\n" + "\n".join(choices))
    return rows[0]


def transcribe_audio(
    audio_path: Path,
    model_size: str,
    device: str,
    compute_type: str,
    language: str,
    beam_size: int,
    vad_filter: bool,
) -> dict[str, Any]:
    WhisperModel = require_faster_whisper()
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments_iter, info = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=beam_size,
        vad_filter=vad_filter,
        initial_prompt="Это аудиозапись экзамена по русскому языку. Распознавай русскую речь точно.",
    )
    segments = [
        {
            "order": index + 1,
            "start": float(segment.start),
            "end": float(segment.end),
            "text": segment.text.strip(),
        }
        for index, segment in enumerate(segments_iter)
    ]
    text = "\n".join(segment["text"] for segment in segments).strip()
    return {
        "model_size": model_size,
        "device": device,
        "compute_type": compute_type,
        "language": language,
        "vad_filter": vad_filter,
        "detected_language": getattr(info, "language", None),
        "language_probability": getattr(info, "language_probability", None),
        "duration": getattr(info, "duration", None),
        "segments": segments,
        "text": text,
    }


def write_outputs(asset: sqlite3.Row, result: dict[str, Any]) -> dict[str, str]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model_name = str(result["model_size"]).replace("\\", "_").replace("/", "_").replace(":", "_")
    vad_suffix = "vad" if result["vad_filter"] else "novad"
    base = f"asset_{asset['id']}_{asset['source_year']}_{asset['segment_order']}_{model_name}_{vad_suffix}"
    json_path = OUTPUT_DIR / f"{base}_asr.json"
    txt_path = OUTPUT_DIR / f"{base}_asr_review.txt"

    payload = {
        "asset": {
            "id": asset["id"],
            "source_year": asset["source_year"],
            "file_path": asset["file_path"],
            "asset_scope": asset["asset_scope"],
            "segment_order": asset["segment_order"],
            "segment_label": asset["segment_label"],
        },
        "asr": result,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    review_lines = [
        f"# ASR Review: {asset['source_year']} {asset['segment_label']}",
        f"# Audio: {asset['file_path']}",
        f"# Model: faster-whisper {result['model_size']} ({result['device']}/{result['compute_type']}, vad={result['vad_filter']})",
        "",
    ]
    for segment in result["segments"]:
        review_lines.append(
            f"[{segment['start']:.2f} - {segment['end']:.2f}] {segment['text']}"
        )
    txt_path.write_text("\n".join(review_lines).strip() + "\n", encoding="utf-8")
    return {"json": str(json_path), "review_txt": str(txt_path)}


def persist_result(conn: sqlite3.Connection, asset: sqlite3.Row, result: dict[str, Any]) -> None:
    transcript_text = result["text"]
    conn.execute(
        """
        INSERT INTO listening_transcripts (
          audio_asset_id, transcript_type, provider, model_name, language,
          transcript_text, confidence
        )
        VALUES (?, 'asr_raw', 'faster-whisper', ?, ?, ?, ?)
        """,
        (
            asset["id"],
            result["model_size"],
            result["language"],
            transcript_text,
            result["language_probability"],
        ),
    )
    conn.execute(
        "DELETE FROM listening_segments WHERE audio_asset_id = ? AND review_status = 'draft'",
        (asset["id"],),
    )
    for segment in result["segments"]:
        conn.execute(
            """
            INSERT INTO listening_segments (
              audio_asset_id, segment_order, start_seconds, end_seconds,
              text_ru, review_status
            )
            VALUES (?, ?, ?, ?, ?, 'draft')
            """,
            (
                asset["id"],
                segment["order"],
                segment["start"],
                segment["end"],
                segment["text"],
            ),
        )
    conn.execute(
        """
        UPDATE listening_assets
        SET asr_status = 'asr_draft',
            transcript_status = 'asr_draft',
            duration_seconds = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (result["duration"], asset["id"]),
    )
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe a listening audio asset with faster-whisper.")
    parser.add_argument("--asset-id", type=int)
    parser.add_argument("--year", type=int)
    parser.add_argument("--segment-order", type=int)
    parser.add_argument("--model-size", default="base", help="faster-whisper model size or local model path.")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--language", default="ru")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--no-vad", action="store_true", help="Disable VAD filtering if speech is over-filtered.")
    parser.add_argument("--persist", action="store_true", help="Write ASR transcript and segments to the database.")
    args = parser.parse_args()

    with connect() as conn:
        asset = find_asset(conn, args.asset_id, args.year, args.segment_order)
        audio_path = ROOT / asset["file_path"]
        if not audio_path.exists():
            raise SystemExit(f"Audio file not found: {audio_path}")

        result = transcribe_audio(
            audio_path=audio_path,
            model_size=args.model_size,
            device=args.device,
            compute_type=args.compute_type,
            language=args.language,
            beam_size=args.beam_size,
            vad_filter=not args.no_vad,
        )
        outputs = write_outputs(asset, result)
        if args.persist:
            persist_result(conn, asset, result)

    print(
        json.dumps(
            {
                "status": "ok",
                "asset_id": asset["id"],
                "source_year": asset["source_year"],
                "segment_order": asset["segment_order"],
                "segments": len(result["segments"]),
                "duration": result["duration"],
                "persisted": args.persist,
                "outputs": outputs,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
