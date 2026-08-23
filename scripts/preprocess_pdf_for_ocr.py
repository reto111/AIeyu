from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw_pdfs"
OUT_DIR = ROOT / "data" / "processed" / "ocr_clean_pdfs"
POPPLER_BIN = (
    Path.home()
    / ".cache"
    / "codex-runtimes"
    / "codex-primary-runtime"
    / "dependencies"
    / "native"
    / "poppler"
    / "Library"
    / "bin"
)


def find_pdftoppm() -> Path:
    bundled = POPPLER_BIN / "pdftoppm.exe"
    if bundled.exists():
        return bundled
    found = shutil.which("pdftoppm")
    if found:
        return Path(found)
    raise RuntimeError("pdftoppm was not found. Install Poppler or use the bundled Codex runtime.")


def render_pdf(input_pdf: Path, image_prefix: Path, dpi: int, first_page: int | None, last_page: int | None) -> None:
    command = [str(find_pdftoppm()), "-png", "-r", str(dpi)]
    if first_page is not None:
        command.extend(["-f", str(first_page)])
    if last_page is not None:
        command.extend(["-l", str(last_page)])
    command.extend([str(input_pdf), str(image_prefix)])
    subprocess.run(command, check=True)


def clean_image(
    image_path: Path,
    output_path: Path,
    threshold: int,
    autocontrast_cutoff: int,
    whiten_bottom_right: bool,
) -> None:
    image = Image.open(image_path).convert("L")
    image = ImageOps.autocontrast(image, cutoff=autocontrast_cutoff)

    # Keep dark printed text and erase light gray diagonal watermarks.
    binary = image.point(lambda value: 0 if value < threshold else 255, mode="1").convert("L")

    if whiten_bottom_right:
        width, height = binary.size
        # Many scanned sheets contain faint social-media watermarks outside the main text area.
        x0 = int(width * 0.68)
        y0 = int(height * 0.88)
        binary.paste(255, (x0, y0, width, height))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    binary.save(output_path)


def images_to_pdf(image_paths: list[Path], output_pdf: Path) -> None:
    if not image_paths:
        raise RuntimeError("No images were rendered from the PDF.")
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    images = [Image.open(path).convert("RGB") for path in image_paths]
    first, rest = images[0], images[1:]
    first.save(output_pdf, save_all=True, append_images=rest, resolution=300.0)
    for image in images:
        image.close()


def preprocess_pdf(
    input_pdf: Path,
    output_dir: Path,
    dpi: int,
    threshold: int,
    autocontrast_cutoff: int,
    first_page: int | None,
    last_page: int | None,
    keep_images: bool,
    whiten_bottom_right: bool,
) -> Path:
    if not input_pdf.exists():
        raise FileNotFoundError(input_pdf)

    stem = input_pdf.stem
    clean_image_dir = output_dir / "page_images" / stem
    output_pdf = output_dir / f"{stem}_ocr_clean.pdf"

    with tempfile.TemporaryDirectory(prefix="ocr_clean_") as temp_name:
        temp_dir = Path(temp_name)
        prefix = temp_dir / "page"
        render_pdf(input_pdf, prefix, dpi, first_page, last_page)
        rendered = sorted(temp_dir.glob("page-*.png"))

        clean_paths: list[Path] = []
        for rendered_path in rendered:
            clean_path = clean_image_dir / rendered_path.name
            clean_image(
                rendered_path,
                clean_path,
                threshold=threshold,
                autocontrast_cutoff=autocontrast_cutoff,
                whiten_bottom_right=whiten_bottom_right,
            )
            clean_paths.append(clean_path)

        images_to_pdf(clean_paths, output_pdf)

        if not keep_images:
            shutil.rmtree(clean_image_dir, ignore_errors=True)

    return output_pdf


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an OCR-friendly PDF by rendering pages and removing light gray watermarks."
    )
    parser.add_argument("input_pdf", help="Input PDF path.")
    parser.add_argument("--out-dir", default=str(OUT_DIR), help="Output directory.")
    parser.add_argument("--dpi", type=int, default=220, help="Render DPI.")
    parser.add_argument(
        "--threshold",
        type=int,
        default=100,
        help="Pixels darker than this become black; lighter pixels become white.",
    )
    parser.add_argument("--autocontrast-cutoff", type=int, default=0, help="Pillow autocontrast cutoff.")
    parser.add_argument("--first-page", type=int, default=None, help="First page to process, 1-based.")
    parser.add_argument("--last-page", type=int, default=None, help="Last page to process, 1-based.")
    parser.add_argument("--keep-images", action="store_true", help="Keep cleaned page PNGs.")
    parser.add_argument(
        "--no-whiten-bottom-right",
        action="store_true",
        help="Do not erase the bottom-right watermark area.",
    )
    args = parser.parse_args()

    output_pdf = preprocess_pdf(
        input_pdf=Path(args.input_pdf),
        output_dir=Path(args.out_dir),
        dpi=args.dpi,
        threshold=args.threshold,
        autocontrast_cutoff=args.autocontrast_cutoff,
        first_page=args.first_page,
        last_page=args.last_page,
        keep_images=args.keep_images,
        whiten_bottom_right=not args.no_whiten_bottom_right,
    )
    print(output_pdf)


if __name__ == "__main__":
    main()
