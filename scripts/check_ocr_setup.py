from pathlib import Path
import subprocess


TESSERACT_EXE = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA_DIR = Path(r"C:\Users\Reto\tesseract-tessdata")


def run_command(args: list[str]) -> str:
    completed = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return (completed.stdout + completed.stderr).strip()


def main() -> None:
    if not TESSERACT_EXE.exists():
        raise SystemExit(f"Tesseract not found: {TESSERACT_EXE}")

    if not TESSDATA_DIR.exists():
        raise SystemExit(f"Tessdata directory not found: {TESSDATA_DIR}")

    version = run_command([str(TESSERACT_EXE), "--version"]).splitlines()[0]
    langs = run_command(
        [str(TESSERACT_EXE), "--tessdata-dir", str(TESSDATA_DIR), "--list-langs"]
    )

    if "rus" not in langs.split():
        raise SystemExit("Russian language data is missing.")

    print(version)
    print(langs)
    print("OCR setup OK")


if __name__ == "__main__":
    main()
