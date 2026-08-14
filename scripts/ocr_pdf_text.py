from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import tempfile

import fitz


TESSERACT_EXE = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA_DIR = Path(r"C:\Users\Reto\tesseract-tessdata")


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


def ocr_pdf(pdf_path: Path, output_path: Path, lang: str, dpi: int, max_pages: int | None) -> None:
    if not TESSERACT_EXE.exists():
        raise SystemExit(f"Tesseract not found: {TESSERACT_EXE}")
    if not TESSDATA_DIR.exists():
        raise SystemExit(f"Tessdata directory not found: {TESSDATA_DIR}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = fitz.open(pdf_path)

    page_count = len(document) if max_pages is None else min(len(document), max_pages)
    parts: list[str] = []

    with tempfile.TemporaryDirectory(prefix="russian_ai_ocr_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        for index in range(page_count):
            image_path = tmp_path / f"page_{index + 1:04d}.png"
            render_page(document[index], image_path, dpi)
            text = ocr_image(image_path, lang)
            parts.append(f"\n\n--- Page {index + 1} ---\n{text}")

    output_path.write_text("\n".join(parts).strip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR a Russian PDF into UTF-8 text.")
    parser.add_argument("pdf", type=Path, help="Input PDF path")
    parser.add_argument("output", type=Path, help="Output UTF-8 text path")
    parser.add_argument("--lang", default="rus+eng", help="Tesseract languages, default: rus+eng")
    parser.add_argument("--dpi", type=int, default=300, help="Render DPI, default: 300")
    parser.add_argument("--max-pages", type=int, default=None, help="Limit pages for a quick test")
    args = parser.parse_args()

    ocr_pdf(args.pdf, args.output, args.lang, args.dpi, args.max_pages)
    print(f"Wrote OCR text: {args.output}")


if __name__ == "__main__":
    main()
