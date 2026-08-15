from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pymupdf as fitz


def authenticate(document: fitz.Document, password: str | None) -> bool:
    if not document.needs_pass:
        return True
    if not password:
        return False
    return bool(document.authenticate(password))


def inspect_pdf(pdf_path: Path, password: str | None, sample_pages: int) -> dict:
    item: dict = {
        "file_name": pdf_path.name,
        "file_path": str(pdf_path),
        "size_bytes": pdf_path.stat().st_size,
        "encrypted": False,
        "authenticated": None,
        "page_count": None,
        "sample_text_chars": 0,
        "sample_image_count": 0,
        "classification": "unknown",
        "error": None,
    }

    try:
        document = fitz.open(pdf_path)
        item["encrypted"] = bool(document.needs_pass)
        authed = authenticate(document, password)
        item["authenticated"] = authed

        if not authed:
            item["classification"] = "locked"
            return item

        item["page_count"] = len(document)
        pages_to_check = min(len(document), sample_pages)
        text_chars = 0
        image_count = 0

        for page_index in range(pages_to_check):
            page = document[page_index]
            text_chars += len(page.get_text("text").strip())
            image_count += len(page.get_images(full=True))

        item["sample_text_chars"] = text_chars
        item["sample_image_count"] = image_count

        if text_chars >= 200:
            item["classification"] = "text_pdf"
        elif image_count > 0:
            item["classification"] = "scanned_or_photo_pdf"
        else:
            item["classification"] = "low_text_pdf"

    except Exception as exc:
        item["error"] = str(exc)
        item["classification"] = "error"

    return item


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect raw PDF files for import readiness.")
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw_pdfs"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/pdf_inventory.json"))
    parser.add_argument("--sample-pages", type=int, default=3)
    parser.add_argument(
        "--password-env",
        default="PDF_PASSWORD",
        help="Environment variable that contains the PDF password.",
    )
    args = parser.parse_args()

    password = os.environ.get(args.password_env)
    pdfs = sorted(args.input_dir.glob("*.pdf"))
    inventory = [inspect_pdf(path, password, args.sample_pages) for path in pdfs]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for item in inventory:
        print(
            f"{item['file_name']}: {item['classification']}, "
            f"encrypted={item['encrypted']}, pages={item['page_count']}, "
            f"text_chars={item['sample_text_chars']}, images={item['sample_image_count']}"
        )
    print(f"Wrote inventory: {args.output}")


if __name__ == "__main__":
    main()
