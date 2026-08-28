from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import pypdfium2 as pdfium


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "data" / "words" / "tem8_russian_words.pdf"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "processed" / "words" / "ocr_text"
DEFAULT_TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
DEFAULT_TESSDATA = ROOT / "tools" / "tessdata"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def page_range(spec: str | None, page_count: int) -> list[int]:
    if not spec:
        return list(range(page_count))
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_raw, end_raw = part.split("-", 1)
            start = max(int(start_raw), 1)
            end = min(int(end_raw), page_count)
            pages.update(range(start - 1, end))
        else:
            page = int(part)
            if 1 <= page <= page_count:
                pages.add(page - 1)
    return sorted(pages)


def render_page(pdf: pdfium.PdfDocument, page_index: int, image_path: Path, dpi: int) -> None:
    page = pdf[page_index]
    scale = dpi / 72
    bitmap = page.render(scale=scale, rotation=0)
    pil_image = bitmap.to_pil()
    pil_image.save(image_path)


def run_tesseract(
    tesseract: Path,
    tessdata: Path,
    image_path: Path,
    output_base: Path,
    lang: str,
    psm: int,
) -> None:
    command = [
        str(tesseract),
        str(image_path),
        str(output_base),
        "--tessdata-dir",
        str(tessdata),
        "-l",
        lang,
        "--psm",
        str(psm),
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR a Russian vocabulary PDF.")
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--prefix",
        default="tem8_russian_words",
        help="Output filename prefix, e.g. tem4_russian_words.",
    )
    parser.add_argument("--tesseract", type=Path, default=DEFAULT_TESSERACT)
    parser.add_argument("--tessdata", type=Path, default=DEFAULT_TESSDATA)
    parser.add_argument("--lang", default="rus+chi_sim")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--psm", type=int, default=6)
    parser.add_argument("--pages", help="1-based pages, e.g. 1-5 or 1,3,8-10")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    pdf_path = args.pdf.resolve()
    output_dir = args.output_dir.resolve()
    page_dir = output_dir / "pages"
    output_dir.mkdir(parents=True, exist_ok=True)
    page_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    if not args.tesseract.exists():
        raise FileNotFoundError(args.tesseract)
    for lang_name in args.lang.split("+"):
        traineddata = args.tessdata / f"{lang_name}.traineddata"
        if not traineddata.exists():
            raise FileNotFoundError(traineddata)

    pdf = pdfium.PdfDocument(str(pdf_path))
    pages = page_range(args.pages, len(pdf))
    manifest = {
        "source_pdf": str(pdf_path),
        "source_sha256": sha256(pdf_path),
        "page_count": len(pdf),
        "requested_pages": [page + 1 for page in pages],
        "lang": args.lang,
        "dpi": args.dpi,
        "psm": args.psm,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "outputs": [],
    }

    with tempfile.TemporaryDirectory(prefix="aieyu_ocr_") as tmp:
        tmp_dir = Path(tmp)
        for page_index in pages:
            page_no = page_index + 1
            text_path = page_dir / f"{args.prefix}_page_{page_no:03d}.txt"
            if text_path.exists() and not args.force:
                text = text_path.read_text(encoding="utf-8", errors="replace")
                manifest["outputs"].append(
                    {"page": page_no, "path": str(text_path), "chars": len(text.strip()), "skipped": True}
                )
                continue

            image_path = tmp_dir / f"page_{page_no:03d}.png"
            output_base = tmp_dir / f"page_{page_no:03d}"
            render_page(pdf, page_index, image_path, args.dpi)
            run_tesseract(args.tesseract, args.tessdata, image_path, output_base, args.lang, args.psm)
            raw_text = output_base.with_suffix(".txt").read_text(encoding="utf-8", errors="replace")
            text_path.write_text(raw_text.strip() + "\n", encoding="utf-8")
            manifest["outputs"].append(
                {"page": page_no, "path": str(text_path), "chars": len(raw_text.strip()), "skipped": False}
            )
            print(f"OCR page {page_no}/{len(pdf)} -> {len(raw_text.strip())} chars")

    combined_path = output_dir / f"{args.prefix}_ocr_combined.txt"
    with combined_path.open("w", encoding="utf-8") as stream:
        for page_index in pages:
            page_no = page_index + 1
            text_path = page_dir / f"{args.prefix}_page_{page_no:03d}.txt"
            if not text_path.exists():
                continue
            stream.write(f"\n\n===== PAGE {page_no:03d} =====\n")
            stream.write(text_path.read_text(encoding="utf-8", errors="replace"))

    manifest["combined_path"] = str(combined_path)
    manifest["finished_at"] = datetime.now().isoformat(timespec="seconds")
    manifest_path = output_dir / f"{args.prefix}_ocr_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pages_done": len(pages), "combined": str(combined_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
