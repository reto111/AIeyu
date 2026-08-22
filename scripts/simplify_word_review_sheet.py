from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "processed" / "words" / "tem8_words_review_cleaned.csv"
DEFAULT_REMOVED = ROOT / "data" / "processed" / "words" / "tem8_words_removed_nonwords.csv"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "words" / "tem8_words_review_simple.csv"
DEFAULT_MANUAL = ROOT / "data" / "processed" / "words" / "tem8_words_needs_manual.csv"

CYRILLIC_WORD_RE = re.compile(r"^[А-Яа-яЁё-]{2,}$")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
RUSSIAN_RE = re.compile(r"[А-Яа-яЁёA-Za-z][А-Яа-яЁёA-Za-z0-9-]*")
NOISE_RE = re.compile(r"[#@№&$%+=<>`\"“”‘’|\\{}\[\]【】]+")

OCR_CHINESE_NOISE = (
    "惧",
    "心",
    "幼",
    "园",
    "倩",
    "魍",
    "疆",
    "啬",
    "夺",
    "茬",
    "纱",
    "乡",
    "踉",
)

REAL_YO_ROOTS = (
    "актёр",
    "берёз",
    "водоём",
    "влюблён",
    "гребён",
    "дёрг",
    "дёрз",
    "дирижёр",
    "еж",
    "ёж",
    "желёз",
    "жёлт",
    "жёст",
    "житьё",
    "зачёрк",
    "застёг",
    "зелён",
    "козёл",
    "лёгк",
    "мёртв",
    "объём",
    "ребён",
    "сёстр",
    "счёт",
    "трёх",
    "чёрн",
    "чёрт",
    "щёт",
)

# Many source entries mark stress, and OCR reads stressed е as ё.
# These roots are kept in е form instead of preserving the OCR artefact.
STRESSED_E_OCR_ROOTS = (
    "абитуриент",
    "агент",
    "агротехник",
    "акцент",
    "акционер",
    "аллея",
    "америк",
    "апрел",
    "арен",
    "аренд",
    "арифмет",
    "артиллер",
    "архитектор",
    "ассистент",
    "ассортимент",
    "ателье",
    "атмосфер",
    "бактер",
    "балет",
    "банкет",
    "батаре",
    "бегл",
    "бедност",
    "бездель",
    "безупреч",
    "белет",
    "белк",
    "белоснеж",
    "бесполез",
    "библиотек",
    "бизнесмен",
    "бледнет",
    "болельщик",
    "букет",
    "бюджет",
    "ведение",
    "ведомств",
    "венгри",
    "верност",
    "верует",
    "верт",
    "весель",
    "вестник",
    "взаимодейств",
    "взамен",
    "взрослет",
    "видеокассет",
    "видеотехник",
    "виднет",
    "вишнев",
    "владел",
    "владени",
    "внедрени",
    "возбуждени",
    "воздейств",
    "возмущени",
    "возникновени",
    "возражени",
    "волшеб",
    "воображени",
    "воплощени",
    "воспалени",
    "восстановлени",
    "восхищени",
    "впоследств",
    "вселен",
    "всемер",
    "высокомер",
    "вычислени",
    "газет",
    "галере",
    "где",
    "гени",
    "генн",
    "геометр",
    "гнев",
    "греческ",
    "грешн",
    "губерни",
    "гудет",
    "декрет",
    "делени",
    "десятилет",
    "диалект",
    "дивиденд",
    "диет",
    "дирекци",
    "дискет",
    "дискотек",
    "дисплей",
    "добавлени",
    "добрососед",
    "дополнени",
    "драгоцен",
    "древес",
    "еврей",
    "европе",
    "земледел",
    "зрел",
    "зрелищ",
    "извест",
    "извещени",
    "изготовлени",
    "издател",
    "издели",
    "измен",
    "изображени",
    "изречени",
    "импери",
    "инвестор",
    "индивидуал",
    "инженер",
    "интеллект",
    "интервент",
    "интернет",
    "инцидент",
    "исключени",
    "исслед",
    "кавалери",
    "казенн",
)


def normalize_word(word: str) -> str:
    word = (word or "").strip()
    word = re.sub(r"[^А-Яа-яЁё-]", "", word)
    return word


def resolve_yo_ocr(word: str) -> tuple[str, str]:
    word = normalize_word(word)
    if "ё" not in word.lower():
        return word, ""

    lower = word.lower()
    if any(root in lower for root in REAL_YO_ROOTS):
        return word, "yo_kept"

    e_word = word.replace("Ё", "Е").replace("ё", "е")
    e_lower = e_word.lower()
    if any(root in e_lower for root in STRESSED_E_OCR_ROOTS):
        return e_word, "yo_to_e_ocr_stress"

    if re.search(r"ени[еяюй]?$|ение|ением|ении|ений|ениях", e_lower):
        return e_word, "yo_to_e_ocr_stress"
    if re.search(r"(ент|ет|ета|етный|ер|ерный|ерия|ейск|еец)$", e_lower):
        return e_word, "yo_to_e_ocr_stress"

    return word, "yo_e_uncertain"


def append_note(notes: str, note: str) -> str:
    notes = (notes or "").strip()
    if not note:
        return notes
    if note in notes.split(";"):
        return notes
    return f"{notes};{note}".strip(";")


def normalize_spaces(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    return text.strip()


def strip_chinese_noise(text: str) -> str:
    text = normalize_spaces(text)
    for noise in OCR_CHINESE_NOISE:
        text = text.replace(noise, "")
    text = NOISE_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^[,，.。:：;；、\s-]+", "", text)
    text = re.sub(r"[,，.。:：;；、\s-]+$", "", text)
    return text.strip()


def remove_examples(text: str) -> str:
    text = normalize_spaces(text)
    first = text
    for marker in ["/", "／", "例", "例如"]:
        if marker in first:
            first = first.split(marker, 1)[0]
    if ":" in first or "：" in first:
        left = re.split(r"[:：]", first, maxsplit=1)[0]
        if CHINESE_RE.search(left):
            first = left
        else:
            first = re.split(r"[:：]", first, maxsplit=1)[1]
    first = first.replace("@@", ";").replace("@", ";").replace("©", ";")
    return first


def core_meaning(text: str) -> str:
    text = remove_examples(text)
    text = RUSSIAN_RE.sub(" ", text)
    text = re.sub(r"\d+", " ", text)
    text = strip_chinese_noise(text)
    if not CHINESE_RE.search(text):
        return ""
    parts = re.split(r"[;；。]", text)
    cleaned_parts: list[str] = []
    for part in parts:
        part = strip_chinese_noise(part)
        if not part or not CHINESE_RE.search(part):
            continue
        cleaned_parts.append(part)
        if len(cleaned_parts) >= 3:
            break
    meaning = "；".join(cleaned_parts) if cleaned_parts else text
    meaning = re.sub(r"\s+", " ", meaning)
    return meaning[:120].strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def simplify_rows(rows: list[dict[str, str]], removed_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    simple: list[dict[str, str]] = []
    manual: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for row in rows:
        word, yo_note = resolve_yo_ocr(row.get("word", ""))
        lemma, lemma_yo_note = resolve_yo_ocr(row.get("lemma", ""))
        meaning = core_meaning(row.get("meaning_zh", ""))
        reason = ""
        page = int(row.get("source_page") or 0)
        if page > 285:
            reason = "phrase_appendix_page"
        elif row.get("auto_confidence") != "high":
            reason = "medium_or_low_confidence"
        elif not CYRILLIC_WORD_RE.match(word):
            reason = "unreliable_word_shape"
        elif not meaning:
            reason = "missing_core_meaning"
        elif yo_note == "yo_e_uncertain":
            reason = "yo_e_uncertain"
        elif (word.lower(), meaning) in seen:
            reason = "duplicate_after_simplify"

        simplified = {
            "source_file": row.get("source_file", ""),
            "source_page": row.get("source_page", ""),
            "block_index": row.get("block_index", ""),
            "word": word,
            "original_word": row.get("original_word") or row.get("word", ""),
            "lemma": lemma,
            "part_of_speech": row.get("part_of_speech", ""),
            "meaning_zh": meaning,
            "raw_meaning_zh": row.get("meaning_zh", ""),
            "auto_confidence": row.get("auto_confidence", ""),
            "auto_notes": append_note(append_note(row.get("auto_notes", ""), yo_note), lemma_yo_note),
            "review_status": "pending",
            "review_notes": row.get("review_notes", ""),
            "manual_reason": reason,
            "raw_headword": row.get("raw_headword", ""),
            "raw_block": row.get("raw_block", ""),
        }
        if reason:
            manual.append(simplified)
            continue
        seen.add((word.lower(), meaning))
        simple.append(simplified)

    for row in removed_rows:
        word, yo_note = resolve_yo_ocr(row.get("word", ""))
        manual.append(
            {
                "source_file": row.get("source_file", ""),
                "source_page": row.get("source_page", ""),
                "block_index": row.get("block_index", ""),
                "word": word,
                "original_word": row.get("original_word") or row.get("word", ""),
                "lemma": "",
                "part_of_speech": row.get("part_of_speech", ""),
                "meaning_zh": core_meaning(row.get("meaning_zh", "")),
                "raw_meaning_zh": row.get("meaning_zh", ""),
                "auto_confidence": row.get("auto_confidence", ""),
                "auto_notes": append_note(row.get("auto_notes", ""), yo_note),
                "review_status": "pending",
                "review_notes": row.get("review_notes", ""),
                "manual_reason": row.get("remove_reason", "removed_nonword"),
                "raw_headword": row.get("raw_headword", ""),
                "raw_block": row.get("raw_block", ""),
            }
        )
    return simple, manual


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a simplified vocabulary review sheet.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--removed", type=Path, default=DEFAULT_REMOVED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manual", type=Path, default=DEFAULT_MANUAL)
    args = parser.parse_args()

    rows = read_csv(args.input)
    removed_rows = read_csv(args.removed)
    simple, manual = simplify_rows(rows, removed_rows)
    fieldnames = [
        "source_file",
        "source_page",
        "block_index",
        "word",
        "original_word",
        "lemma",
        "part_of_speech",
        "meaning_zh",
        "raw_meaning_zh",
        "auto_confidence",
        "auto_notes",
        "review_status",
        "review_notes",
        "manual_reason",
        "raw_headword",
        "raw_block",
    ]
    write_csv(args.output, simple, fieldnames)
    write_csv(args.manual, manual, fieldnames)
    print(
        {
            "input_rows": len(rows),
            "simple_rows": len(simple),
            "manual_rows": len(manual),
            "output": str(args.output),
            "manual": str(args.manual),
        }
    )


if __name__ == "__main__":
    main()
