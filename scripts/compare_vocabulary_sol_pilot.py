"""Validate pilot output and list differences; never grade meaning by string equality."""
import argparse
import json
import unicodedata
from pathlib import Path


def compare(reference, result):
    expected = {row["key"]: row["reference"] for row in reference}
    keys = [row["key"] for row in result]
    if len(keys) != len(set(keys)) or set(keys) != set(expected):
        raise ValueError("Missing, duplicate or unexpected sample keys")
    differences = []
    counts = {"keep": 0, "fix": 0, "review": 0}
    for row in result:
        for field in ("word", "accent", "part", "meaning", "pair", "status", "reason"):
            if not isinstance(row.get(field), str):
                raise ValueError(f"{row['key']}: missing/non-text {field}")
        if row["status"] not in counts:
            raise ValueError(f"{row['key']}: invalid status")
        counts[row["status"]] += 1
        old = expected[row["key"]]
        changed = {}
        for field, source in (("word", "canonical"), ("accent", "accent"),
                              ("part", "part"), ("meaning", "meaning"), ("pair", "perfective")):
            actual = unicodedata.normalize("NFC", row[field])
            baseline = unicodedata.normalize("NFC", old[source])
            if actual != baseline:
                changed[field] = {"baseline": baseline, "candidate": actual}
        if changed or row["status"] == "review":
            differences.append({"key": row["key"], "id": old["id"],
                                "differences": changed, "reason": row["reason"]})
    return {"count": len(result), "decisions": counts,
            "warning": "Differences are not error scores; semantic and aspect review required.",
            "differences": differences}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    reference = json.loads((root / "data/review_samples/sol_pilot_20260912/reference.json").read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    print(json.dumps(compare(reference, result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
