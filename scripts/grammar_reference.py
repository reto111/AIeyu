"""Resumable local OCR and source-grounded grammar retrieval. No network calls.

OCR is never implicitly reviewed. Review batches contain visually checked page
fragments; only complete sections without unresolved notes enter retrieval.
The dedicated database never opens the student database.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time
import unicodedata

from extract_pdf_text import ocr_image, render_page
from knowledge_base import file_sha256

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data/knowledge_sources/Russian_grammar_reference_scan.pdf"
WORK = ROOT / "data/processed/grammar_reference"
DB = WORK / "grammar_reference.sqlite"


def now():
    return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def strip_search_formatting(text):
    # Emphasis/code markers can occur inside an inflected Russian word.
    # Keep the reviewed body intact; this is only a search representation.
    return text.translate({ord('*'): None, ord('`'): None})


def normalize(text):
    # Ignore stress for search, retain ё and the exact source spelling in body.
    return "".join(c for c in unicodedata.normalize("NFD", strip_search_formatting(text).lower()) if c != "\u0301")


def schema(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS source (
      id INTEGER PRIMARY KEY CHECK(id=1), path TEXT NOT NULL,
      sha256 TEXT NOT NULL, total_pages INTEGER NOT NULL, title TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS pages (
      pdf_page INTEGER PRIMARY KEY, printed_page TEXT,
      review_json TEXT NOT NULL, review_sha256 TEXT NOT NULL,
      batch_id TEXT NOT NULL, reviewed_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS chunks (
      code TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL,
      pdf_pages TEXT NOT NULL, printed_pages TEXT NOT NULL,
      status TEXT NOT NULL CHECK(status IN ('ready','incomplete','unresolved')),
      notes TEXT NOT NULL, search_text TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS batches (
      id TEXT PRIMARY KEY, sha256 TEXT NOT NULL, imported_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS page_revisions (
      id INTEGER PRIMARY KEY, pdf_page INTEGER NOT NULL,
      previous_json TEXT NOT NULL, previous_sha256 TEXT NOT NULL,
      previous_batch_id TEXT NOT NULL, correction_batch_id TEXT NOT NULL,
      reason TEXT NOT NULL, corrected_at TEXT NOT NULL);
    """)


def ocr(pages, dpi=220):
    import pymupdf
    WORK.mkdir(parents=True, exist_ok=True)
    fingerprint = file_sha256(PDF)
    with pymupdf.open(PDF) as doc:
        for page in pages:
            if not 1 <= page <= len(doc):
                raise ValueError(f"Invalid page {page}")
            target = WORK / "ocr" / f"p{page:04d}.json"
            if target.exists():
                old = json.loads(target.read_text(encoding="utf-8"))
                if old["source_sha256"] != fingerprint:
                    raise ValueError("Source PDF changed; do not reuse old OCR")
                continue
            started = time.perf_counter()
            image = WORK / "renders" / f"p{page:04d}.png"
            image.parent.mkdir(parents=True, exist_ok=True)
            render_page(doc[page-1], image, dpi)
            text = ocr_image(image, "chi_sim+rus+eng")
            seconds = round(time.perf_counter() - started, 3)
            dump(target, dict(pdf_page=page, source_sha256=fingerprint,
                 dpi=dpi, engine="tesseract", languages="chi_sim+rus+eng",
                 psm=6, status="unreviewed", seconds=seconds, created_at=now(), text=text))
            print(json.dumps(dict(page=page, seconds=seconds, chars=len(text))), flush=True)


def validate_batch(batch, fingerprint, total_pages):
    if batch["source_sha256"] != fingerprint:
        raise ValueError("Review belongs to a different PDF")
    if not batch.get("batch_id") or not batch.get("pages"):
        raise ValueError("Empty batch")
    seen = set()
    for page in batch["pages"]:
        number = page["pdf_page"]
        if number in seen or not 1 <= number <= total_pages:
            raise ValueError(f"Duplicate or invalid page: {number}")
        seen.add(number)
        if page.get("review_method") != "visual_comparison":
            raise ValueError("Explicit visual review required")
        if not page.get("fragments"):
            raise ValueError("No page fragments")
        codes = set()
        for part in page["fragments"]:
            if part["code"] in codes or not part["body"].strip() or not part["title"].strip():
                raise ValueError("Duplicate or empty fragment")
            codes.add(part["code"])
            if not isinstance(part["start"], bool) or not isinstance(part["end"], bool):
                raise ValueError("Explicit section boundaries required")


def rebuild_chunks(conn):
    sections = {}
    for row in conn.execute("SELECT review_json FROM pages ORDER BY pdf_page"):
        page = json.loads(row[0])
        for part in page["fragments"]:
            sections.setdefault(part["code"], []).append((page, part))
    conn.execute("DELETE FROM chunks")
    for code, parts in sections.items():
        numbers = [p["pdf_page"] for p, _ in parts]
        titles = {part["title"] for _, part in parts}
        if len(titles) != 1:
            raise ValueError(f"Conflicting section title: {code}")
        if any(part["start"] for _, part in parts[1:]) or any(part["end"] for _, part in parts[:-1]):
            raise ValueError(f"Conflicting section boundaries: {code}")
        notes = [note for page, part in parts for note in page.get("unresolved", []) + part.get("unresolved", [])]
        complete = parts[0][1]["start"] and parts[-1][1]["end"] and numbers == list(range(numbers[0], numbers[-1]+1))
        status = "unresolved" if notes else "ready" if complete else "incomplete"
        # Concatenation reconstructs a sentence split by a page boundary. Explicit
        # paragraph newlines live in the reviewed fragments, not in this join.
        body = "".join(part["body"] for _, part in parts)
        title = parts[0][1]["title"]
        conn.execute("INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?)", (
            code, title, body, json.dumps(numbers),
            json.dumps([p.get("printed_page") for p, _ in parts], ensure_ascii=False),
            status, json.dumps(notes, ensure_ascii=False), normalize(title + "\n" + body)))


def import_batch(path, db=DB, apply=False, pdf=PDF, title="当代俄语语法（张会森，2010）"):
    import pymupdf
    batch = json.loads(Path(path).read_text(encoding="utf-8"))
    fingerprint = file_sha256(pdf)
    with pymupdf.open(pdf) as doc:
        total_pages = len(doc)
    validate_batch(batch, fingerprint, total_pages)
    batch_hash = hashlib.sha256(json.dumps(batch, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    # Preview and validate on an in-memory snapshot. No schema changes on disk.
    preview = sqlite3.connect(":memory:")
    db = Path(db)
    if db.exists():
        with closing(sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True)) as src:
            src.backup(preview)
    schema(preview)
    source = preview.execute("SELECT sha256 FROM source").fetchone()
    if source and source[0] != fingerprint:
        raise ValueError("Database source fingerprint differs")
    old_batch = preview.execute("SELECT sha256 FROM batches WHERE id=?", (batch["batch_id"],)).fetchone()
    if old_batch:
        if old_batch[0] != batch_hash:
            raise ValueError("Existing batch is immutable; do not overwrite review evidence")
        return dict(batch=batch["batch_id"], result="already_imported", new_pages=0)
    corrections = {}
    for page in batch["pages"]:
        old = preview.execute("SELECT review_json,review_sha256,batch_id FROM pages WHERE pdf_page=?", (page["pdf_page"],)).fetchone()
        if old:
            if page.get("expected_review_sha256") != old[1] or not page.get("correction_reason"):
                raise ValueError(f"Page already reviewed: {page['pdf_page']}; explicit correction with matching hash needed")
            corrections[page["pdf_page"]] = old
        elif page.get("expected_review_sha256"):
            raise ValueError("Cannot correct a page missing from database")
    preview.execute("INSERT OR IGNORE INTO source VALUES (1,?,?,?,?)", (pdf.as_posix(), fingerprint, total_pages, title))
    for page in batch["pages"]:
        data = json.dumps(page, ensure_ascii=False, sort_keys=True)
        if page["pdf_page"] in corrections:
            old = corrections[page["pdf_page"]]
            preview.execute("INSERT INTO page_revisions (pdf_page,previous_json,previous_sha256,previous_batch_id,correction_batch_id,reason,corrected_at) VALUES (?,?,?,?,?,?,?)",
                (page["pdf_page"], *old, batch["batch_id"], page["correction_reason"], now()))
        preview.execute("INSERT OR REPLACE INTO pages VALUES (?,?,?,?,?,?)", (page["pdf_page"], page.get("printed_page"), data,
            hashlib.sha256(data.encode()).hexdigest(), batch["batch_id"], now()))
    preview.execute("INSERT INTO batches VALUES (?,?,?)", (batch["batch_id"], batch_hash, now()))
    rebuild_chunks(preview)
    preview.commit()
    counts = dict(preview.execute("SELECT status,COUNT(*) FROM chunks GROUP BY status"))
    result = dict(batch=batch["batch_id"], new_pages=len(batch["pages"])-len(corrections), corrected_pages=len(corrections), chunks=counts, applied=apply)
    if apply:
        db.parent.mkdir(parents=True, exist_ok=True)
        if db.exists():
            backup = db.parent / "backups" / f"grammar_{datetime.now():%Y%m%d_%H%M%S_%f}.sqlite"
            backup.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(db)) as source_conn, closing(sqlite3.connect(backup)) as backup_conn:
                source_conn.backup(backup_conn)
            result["backup"] = str(backup)
        # SQLite backup replaces the dedicated DB atomically under SQLite locks.
        # OCR never writes this DB; review imports are intentionally single writer.
        with closing(sqlite3.connect(db)) as destination:
            preview.backup(destination)
    preview.close()
    return result


def search(query, limit=5, db=DB):
    terms = [term for t in query.split() if (term := normalize(t))]
    if not terms or limit < 1:
        return []
    with closing(sqlite3.connect(f"{Path(db).resolve().as_uri()}?mode=ro", uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        source = dict(conn.execute("SELECT * FROM source").fetchone())
        scored = []
        for row in conn.execute("SELECT * FROM chunks WHERE status='ready'"):
            # Also handle cached indexes created before formatting was stripped.
            search_text = strip_search_formatting(row["search_text"])
            hits = [t for t in terms if t in search_text]
            if len(hits) != len(terms):
                continue
            score = sum(min(search_text.count(t), 5) + 5 * (t in normalize(row["title"])) for t in hits)
            if normalize(row['title']).split(' ', 2)[-1] == normalize(query.strip()):
                score += 50
            pages = json.loads(row["pdf_pages"])
            scored.append(dict(code=row["code"], title=row["title"], body=row["body"], score=score,
                matched_terms=hits, pdf_pages=pages, printed_pages=json.loads(row["printed_pages"]),
                citation=f"{source['title']}，PDF {pages[0]}–{pages[-1]} 页",
                source_path=source["path"], source_sha256=source["sha256"], review_status="visual_checked"))
    return sorted(scored, key=lambda x: (-x["score"], x["code"]))[:limit]


def status(db=DB):
    result = dict(ocr_pages=len(list((WORK / "ocr").glob("p*.json"))))
    if Path(db).exists():
        with closing(sqlite3.connect(f"{Path(db).resolve().as_uri()}?mode=ro", uri=True)) as conn:
            result.update(reviewed_pages=[r[0] for r in conn.execute("SELECT pdf_page FROM pages ORDER BY pdf_page")],
                chunks=dict(conn.execute("SELECT status,COUNT(*) FROM chunks GROUP BY status")),
                integrity=conn.execute("PRAGMA integrity_check").fetchone()[0])
    return result


def export_review(db=DB):
    """Readable local inspection artifact, including excluded/incomplete sections."""
    lines = ['# 当代俄语语法：已清洗页与待办', '',
             '这是原图对照转写，不是全书完成或零错误证明。未决与不完整章节不进入检索。', '']
    with closing(sqlite3.connect(f"{Path(db).resolve().as_uri()}?mode=ro", uri=True)) as conn:
        for number, data in conn.execute('SELECT pdf_page,review_json FROM pages ORDER BY pdf_page'):
            page = json.loads(data)
            lines.extend([f'## PDF {number} / 印刷 {page.get("printed_page")}', ''])
            for part in page['fragments']:
                lines.extend([f'### {part["title"]}', '', part['body'], ''])
                for note in part.get('unresolved', []) + page.get('unresolved', []):
                    lines.extend([f'> 待确认：{note}', ''])
        lines.extend(['## 尚未完整的知识节', ''])
        for title, pages in conn.execute("SELECT title,pdf_pages FROM chunks WHERE status='incomplete'"):
            lines.append(f'- {title}；已转写 PDF 页：{pages}')
    path = Path(db).parent / 'reviewed_pages.md'
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return dict(path=str(path))


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("ocr")
    p.add_argument("--pages", help="Comma-separated page numbers, processed before the range")
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--end", type=int, default=641)
    p.add_argument("--dpi", type=int, default=220)
    p = sub.add_parser("import")
    p.add_argument("batch", type=Path)
    p.add_argument("--apply", action="store_true")
    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=5)
    sub.add_parser("status")
    sub.add_parser("export")
    args = parser.parse_args()
    if args.command == "ocr":
        priority = [int(p) for p in (args.pages or "").split(",") if p]
        ocr(list(dict.fromkeys(priority + list(range(args.start, args.end+1)))), args.dpi)
        return
    result = import_batch(args.batch, apply=args.apply) if args.command == "import" else search(args.query, args.limit) if args.command == "search" else export_review() if args.command == "export" else status()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
