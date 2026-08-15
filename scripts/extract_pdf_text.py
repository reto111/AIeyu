from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import tempfile

import pymupdf as fitz


TESSERACT_EXE = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA_DIR = Path(r"C:\Users\Reto\tesseract-tessdata")


def authenticate(document: fitz.Document, password: str | None) -> bool:
    if not document.needs_pass:
        return True
    if not password:
        return False
    return bool(document.authenticate(password))


def ocr_image(image_path: Path, lang: str) -> str:
    completed = subprocess.run(
        [
            str(TESSERACT_EXE),
            str(image_path),
            "stdout",
            "--tessdata-dir",
            str(TESSDATA_DIR),
            "-l",
            lang,
            "--psm",
            "6",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def render_page(page: fitz.Page, output_path: Path, dpi: int) -> None:
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    pixmap.save(output_path)


def extract_pdf(
    pdf_path: Path,
    output_path: Path,
    password: str | None,
    mode: str,
    lang: str,
    dpi: int,
    max_pages: int | None,
) -> None:
    document = fitz.open(pdf_path)
    if not authenticate(document, password):
        raise SystemExit(f"PDF needs a password and could not be opened: {pdf_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    page_count = len(document) if max_pages is None else min(len(document), max_pages)
    parts: list[str] = []

    with tempfile.TemporaryDirectory(prefix="russian_ai_pdf_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        for index in range(page_count):
            page = document[index]
            direct_text = page.get_text("text").strip()

            should_ocr = mode == "ocr" or (mode == "auto" and len(direct_text) < 50)
            if should_ocr:
                image_path = tmp_path / f"page_{index + 1:04d}.png"
                render_page(page, image_path, dpi)
                page_text = ocr_image(image_path, lang)
                method = "ocr"
            else:
                page_text = direct_text
                method = "direct"

            parts.append(f"\n\n--- Page {index + 1} ({method}) ---\n{page_text}")

    output_path.write_text("\n".join(parts).strip() + "\n", encoding="utf-8")
    print(f"Wrote text: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract text from PDF with optional OCR fallback.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=["auto", "direct", "ocr"], default="auto")
    parser.add_argument("--lang", default="rus+eng")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--password-env", default="PDF_PASSWORD")
    args = parser.parse_args()

    extract_pdf(
        pdf_path=args.pdf,
        output_path=args.output,
        password=os.environ.get(args.password_env),
        mode=args.mode,
        lang=args.lang,
        dpi=args.dpi,
        max_pages=args.max_pages,
    )


if __name__ == "__main__":
    main()
