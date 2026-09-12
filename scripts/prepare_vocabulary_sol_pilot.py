"""Build a reproducible, read-only vocabulary audit pilot from saved snapshots."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    records = []
    for batch in (43, 44, 45):
        path = ROOT / f"data/review_samples/learning_batch_{batch:03d}_catalog.json"
        records.extend(json.loads(path.read_text(encoding="utf-8"))["records"])
    # Evidence marks targeted historical cases, not a proven error label.
    targeted = [r for r in records if r.get("evidence")]
    ordinary = [r for r in records if not r.get("evidence")]
    rng = random.Random(20260912)
    selected = targeted + rng.sample(ordinary, 100 - len(targeted))
    rng.shuffle(selected)
    inputs = []
    reference = []
    for index, record in enumerate(selected, 1):
        key = f"P{index:03d}"
        old = record["original"]
        inputs.append({"key": key, "word": old["word"],
                       "part": old["part_of_speech"], "meaning": old["meaning_zh"]})
        reference.append({"key": key, "targeted": bool(record.get("evidence")),
                          "reference": record})
    out = ROOT / "data/review_samples/sol_pilot_20260912"
    out.mkdir(exist_ok=True)
    for name, value in (("input.json", inputs), ("reference.json", reference)):
        path = out / name
        if path.exists():
            raise SystemExit(f"Refusing to overwrite {path}")
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"count": len(inputs), "targeted": len(targeted),
                      "ordinary": 100 - len(targeted), "database_written": False}))


if __name__ == "__main__":
    main()
