from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import pymupdf as fitz


TESSERACT_EXE = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA_DIR = Path(r"C:\Users\Reto\tesseract-tessdata")


def sample_pages(pdf_path: Path, pages: list[int], lang: str, dpi: int, chars: int) -> None:
    document = fitz.open(pdf_path)
    direct_chars = sum(
        len(document[index].get_text("text").strip())
        for index in range(min(3, len(document)))
    )
    print(f"FILE {pdf_path.name}")
    print(f"PAGES {len(document)}")
    print(f"DIRECT_TEXT_CHARS_FIRST3 {direct_chars}")

    with tempfile.TemporaryDirectory(prefix="aieyu_pdf_sample_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        for page_number in pages:
            if page_number < 1 or page_number > len(document):
                print(f"PAGE {page_number} SKIPPED")
                continue
            page = document[page_number - 1]
            image_path = tmp_path / f"page_{page_number:04d}.png"
            matrix = fitz.Matrix(dpi / 72, dpi / 72)
            page.get_pixmap(matrix=matrix, alpha=False).save(image_path)
            result = subprocess.run(
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
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            text = " ".join(result.stdout.split())
            print(f"PAGE {page_number} OCR_CHARS {len(result.stdout.strip())}")
            print(text[:chars])


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="OCR sample pages from a scanned PDF.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pages", default="5,10,20")
    parser.add_argument("--lang", default="rus+eng")
    parser.add_argument("--dpi", type=int, default=220)
    parser.add_argument("--chars", type=int, default=500)
    args = parser.parse_args()
    pages = [int(item.strip()) for item in args.pages.split(",") if item.strip()]
    sample_pages(args.pdf, pages, args.lang, args.dpi, args.chars)


if __name__ == "__main__":
    main()
