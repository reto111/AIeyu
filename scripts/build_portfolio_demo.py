"""Build a deterministic, allowlisted offline portfolio attachment (stdlib only)."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "apps" / "portfolio_demo"
OUT = ROOT / "dist" / "portfolio"


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    html = (SOURCE / "index.html").read_text(encoding="utf-8")
    html = html.replace('<link rel="stylesheet" href="style.css">',
                        '<style>\n' + (SOURCE / "style.css").read_text(encoding="utf-8") + '\n</style>')
    html = html.replace('<script src="demo.js"></script>',
                        '<script>\n' + (SOURCE / "demo.js").read_text(encoding="utf-8") + '\n</script>')
    files = {"AIeyu-demo.html": html.encode("utf-8"),
             "README.md": (SOURCE / "README.md").read_bytes(),
             "PROJECT.md": (ROOT / "docs" / "portfolio_demo.md").read_bytes()}
    # Screenshots are explicit demo-only artifacts, never a recursive directory copy.
    for name in ("preview.png", "feedback.png", "mobile.png"):
        path = SOURCE / name
        if path.exists():
            files[name] = path.read_bytes()
    manifest = {name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                for name, data in files.items()}
    files["MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    for name, data in files.items():
        (OUT / name).write_bytes(data)
    archive = OUT / "AIeyu-portfolio-demo.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 27, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            package.writestr(info, data)
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None
        assert set(package.namelist()) == set(files)
    print(json.dumps({"archive": str(archive), "bytes": archive.stat().st_size,
                      "files": list(files)}, ensure_ascii=False))


if __name__ == "__main__":
    build()
