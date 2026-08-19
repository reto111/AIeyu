from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from knowledge_base import (
    ROOT,
    connect,
    ensure_knowledge_base_tables,
    fetch_tem8_ids,
    file_sha256,
    relative_to_root,
)


DEFAULT_SOURCE_DIR = ROOT / "data" / "knowledge_sources" / "tem8"


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, str] = {}
    for raw_line in parts[1].splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, parts[2].strip()


def split_chunks(body: str) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []
    current_title = "全文"
    current_lines: list[str] = []

    for line in body.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            if current_lines:
                chunks.append({"title": current_title, "body": "\n".join(current_lines).strip()})
            current_title = heading.group(1).strip()
            current_lines = []
            continue
        current_lines.append(line)

    if current_lines:
        chunks.append({"title": current_title, "body": "\n".join(current_lines).strip()})

    return [item for item in chunks if item["body"]]


def parse_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in re.split(r"[,，]", value) if item.strip()]


def chunk_code_from_title(title: str) -> str | None:
    match = re.search(r"\[([a-z0-9_.-]+)\]", title)
    return match.group(1) if match else None


def approx_token_count(text: str) -> int:
    return max(len(text) // 2, 1)


def upsert_source(conn, exam_system_id: int, level_id: int, path: Path, meta: dict[str, str]) -> int:
    rel_path = relative_to_root(path)
    title = meta.get("title") or path.stem
    source_type = meta.get("source_type") or "manual_note"
    language = meta.get("language") or "zh"
    trust_level = int(meta.get("trust_level") or 2)
    review_status = meta.get("review_status") or "draft"
    notes = meta.get("notes")
    file_hash = file_sha256(path)

    existing = conn.execute(
        "SELECT id FROM knowledge_sources WHERE exam_system_id = ? AND file_path = ?",
        (exam_system_id, rel_path),
    ).fetchone()
    if existing:
        source_id = int(existing["id"])
        conn.execute(
            """
            UPDATE knowledge_sources
            SET level_id = ?, title = ?, source_type = ?, file_hash = ?, language = ?,
                trust_level = ?, review_status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (level_id, title, source_type, file_hash, language, trust_level, review_status, notes, source_id),
        )
        return source_id

    cursor = conn.execute(
        """
        INSERT INTO knowledge_sources (
          exam_system_id, level_id, title, source_type, file_path, file_hash,
          language, trust_level, review_status, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (exam_system_id, level_id, title, source_type, rel_path, file_hash, language, trust_level, review_status, notes),
    )
    return int(cursor.lastrowid)


def import_file(conn, exam_system_id: int, level_id: int, path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)
    source_id = upsert_source(conn, exam_system_id, level_id, path, meta)
    conn.execute("DELETE FROM knowledge_chunks WHERE source_id = ?", (source_id,))

    question_type_code = meta.get("question_type")
    language = meta.get("language") or "zh"
    review_status = meta.get("review_status") or "draft"
    tags = parse_list(meta.get("tags"))
    default_points = parse_list(meta.get("knowledge_points"))
    imported = 0

    for index, chunk in enumerate(split_chunks(body), start=1):
        chunk_code = chunk_code_from_title(chunk["title"])
        point_code = chunk_code if chunk_code in default_points else (default_points[0] if default_points else chunk_code)
        conn.execute(
            """
            INSERT INTO knowledge_chunks (
              source_id, exam_system_id, level_id, chunk_code, title, body, language,
              question_type_code, knowledge_point_code, tags_json, source_locator,
              token_count, review_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                exam_system_id,
                level_id,
                chunk_code,
                chunk["title"],
                chunk["body"],
                language,
                question_type_code,
                point_code,
                json.dumps(tags, ensure_ascii=False),
                f"{relative_to_root(path)}#chunk-{index}",
                approx_token_count(chunk["body"]),
                review_status,
            ),
        )
        imported += 1

    return {"file": relative_to_root(path), "chunks": imported}


def import_sources(source_dir: Path = DEFAULT_SOURCE_DIR) -> dict[str, Any]:
    paths = sorted(path for path in source_dir.glob("*.md") if path.name.lower() != "readme.md")
    with connect() as conn:
        ensure_knowledge_base_tables(conn)
        exam_system_id, level_id = fetch_tem8_ids(conn)
        results = [import_file(conn, exam_system_id, level_id, path) for path in paths]
        conn.commit()
    return {"source_dir": relative_to_root(source_dir), "files": len(paths), "results": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Markdown knowledge sources into knowledge_chunks.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    args = parser.parse_args()
    print(json.dumps(import_sources(args.source_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
