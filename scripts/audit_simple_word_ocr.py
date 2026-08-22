from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "processed" / "words" / "tem8_words_review_simple.csv"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "words" / "tem8_words_simple_ocr_audit.csv"

VOWELS = set("аеёиоуыэюяАЕЁИОУЫЭЮЯ")
CYRILLIC_WORD_RE = re.compile(r"^[А-Яа-яЁё-]+$")
CONSONANT_CLUSTER_RE = re.compile(r"[бвгджзклмнпрстфхцчшщ]{6,}", re.IGNORECASE)
CONSONANTS = set("бвгджзклмнпрстфхцчшщБВГДЖЗКЛМНПРСТФХЦЧШЩ")
ACRONYMS = {"СССР", "ФРГ", "КНР", "ООН", "НОАК", "ИТАР-ТАСС"}


FIELDNAMES = [
    "source_file",
    "source_page",
    "block_index",
    "current_word",
    "suggested_word",
    "suggested_meaning_zh",
    "action",
    "confidence",
    "risk_score",
    "reasons",
    "basis",
    "original_word",
    "part_of_speech",
    "raw_meaning_zh",
    "raw_headword",
    "raw_block",
]


KNOWN_CORRECTIONS: dict[str, tuple[str, str, str]] = {
    "абаж": ("абажур", "high", "raw_block_contains_inflected_form_abажуром;meaning_lampshade"),
    "абрикбс": ("абрикос", "high", "meaning_apricot"),
    "авантюрйист": ("авантюрист", "high", "known_word_adventurer"),
    "агитания": ("агитация", "high", "meaning_propaganda"),
    "агрессйвный": ("агрессивный", "high", "known_adjective"),
    "алкоголйзм": ("алкоголизм", "high", "known_word_alcoholism"),
    "алкогбОлик": ("алкоголик", "high", "known_word_alcoholic"),
    "анализйровать": ("анализировать", "high", "known_verb"),
    "аналогйчный": ("аналогичный", "high", "known_adjective"),
    "ангйна": ("ангина", "high", "known_word_tonsillitis"),
    "армяЯнский": ("армянский", "high", "known_adjective"),
    "артиллерййский": ("артиллерийский", "high", "known_adjective"),
    "астронбом": ("астроном", "high", "meaning_astronomer"),
    "Атлантическийокеан": ("Атлантический океан", "high", "missing_space_geographical_name"),
    "социал-демократйческий-ая": ("социал-демократический", "high", "dictionary_adjective_remove_feminine_variant"),
    "бИОПОГЙчеСКИЙ": ("биологический", "high", "meaning_biological"),
    "дДОйТЬ": ("доить", "high", "meaning_to_milk"),
    "наякартйна": ("", "high", "phrase_fragment_from_zagadochnaya_kartina"),
    "шльныйистбчник": ("", "high", "phrase_fragment_from_mineralny_istochnik"),
    "подробсток": ("подросток", "high", "meaning_teenager"),
    "полбска": ("полоска", "high", "meaning_strip_or_column"),
    "полубстров": ("полуостров", "high", "meaning_peninsula"),
    "пылесбс": ("пылесос", "high", "meaning_vacuum_cleaner"),
    "НЫоЛОНОЙрылеть": ("", "high", "phrase_fragment_from_rukovodstvovatsya_pravilami"),
    "зйн-складЖ": ("склад", "high", "meaning_warehouse"),
    "сЛоМмйТЬ": ("сломить", "high", "meaning_break_or_overcome"),
    "стрбчка": ("строчка", "high", "meaning_printed_line"),
    "упбрство": ("упорство", "high", "meaning_persistence"),
    "относйтТЬ": ("относить", "high", "known_verb"),
    "беспокОЙйный": ("беспокойный", "high", "known_adjective"),
    "ЖИвоПйсНЫйЙ": ("живописный", "high", "known_adjective"),
    "лжйвЫый": ("лживый", "high", "known_adjective"),
    "СТИХИЙНЫЙЙ": ("стихийный", "high", "known_adjective"),
    "СТОЙКИй": ("стойкий", "high", "known_adjective"),
    "Индййскийокеан": ("Индийский океан", "high", "missing_space_geographical_name"),
    "Тихийокеан": ("Тихий океан", "high", "missing_space_geographical_name"),
    "залйв": ("залив", "high", "meaning_bay"),
    "ВЫЛИТЫый": ("вылитый", "high", "known_adjective"),
    "донскоОйЙ": ("донской", "high", "known_adjective"),
    "исхОднЫый": ("исходный", "high", "known_adjective"),
    "лиходЙ": ("лихой", "high", "known_adjective"),
    "мОЩНЫйЙ": ("мощный", "high", "known_adjective"),
    "обвинйЯть": ("обвинять", "high", "known_verb"),
    "ОВвсЯнНЫый": ("овсяный", "high", "known_adjective"),
    "ОТЦОВсКИЙй": ("отцовский", "high", "known_adjective"),
    "пшшенйичный": ("пшеничный", "high", "known_adjective"),
    "атейст": ("атеист", "high", "meaning_atheist"),
    "бойзнь": ("боязнь", "high", "meaning_fear"),
    "веройтность": ("вероятность", "high", "meaning_probability"),
    "дойрка": ("доярка", "high", "meaning_milkmaid"),
    "ймпорт": ("импорт", "high", "meaning_import"),
    "ймпортный": ("импортный", "high", "meaning_import_adjective"),
    "йИндекс": ("индекс", "high", "meaning_index"),
    "йней": ("иней", "high", "meaning_hoarfrost"),
    "интуйция": ("интуиция", "high", "meaning_intuition"),
    "конструйровать": ("конструировать", "high", "meaning_design_or_construct"),
    "неприяйтный": ("неприятный", "high", "known_adjective"),
    "нерешийтельный": ("нерешительный", "high", "known_adjective"),
    "покбойный": ("покойный", "high", "meaning_deceased"),
    "пострбойка": ("постройка", "high", "meaning_building"),
    "прозайческий": ("прозаический", "high", "meaning_prosaic"),
    "реконструйровать": ("реконструировать", "high", "meaning_reconstruct"),
    "спокбойствие": ("спокойствие", "high", "meaning_calmness"),
    "термойдерный": ("термоядерный", "high", "meaning_thermonuclear"),
    "Украйна": ("Украина", "high", "meaning_ukraine"),
    "устойть": ("устоять", "high", "meaning_stand_firm"),
    "хоккейст": ("хоккеист", "high", "meaning_hockey_player"),
    "тийшка": ("шишка", "high", "meaning_cone"),
    "эвакуйровать": ("эвакуировать", "high", "meaning_evacuate"),
    "эгойзм": ("эгоизм", "high", "meaning_egoism"),
    "займствовать": ("заимствовать", "high", "meaning_borrow_adopt"),
    "естёственныйводоём": ("естественный водоём", "high", "missing_space_phrase"),
    "нейсныемысли": ("", "high", "phrase_fragment_from_neyasnye_mysli"),
    "пльскийспрос": ("", "high", "phrase_fragment_from_consumer_demand"),
    "ЖЖ": ("", "high", "sentence_fragment_from_valyatsya_example"),
    "тьй": ("", "high", "headword_fragment_not_reliable"),
    "шб": ("", "high", "sentence_fragment_from_proverb_example"),
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def visual_normalize(word: str) -> str:
    if word in ACRONYMS:
        return word
    force_lower = word.isupper() and len(word) > 3
    if any(char.isupper() for char in word[1:]):
        force_lower = True
    if force_lower:
        word = word.lower()
    replacements = {
        "О": "о",
        "И": "и",
        "Й": "й",
        "Я": "я",
        "Ч": "ч",
        "Щ": "щ",
        "С": "с",
        "В": "в",
        "Д": "д",
        "Ж": "ж",
        "З": "з",
        "К": "к",
        "Л": "л",
        "М": "м",
        "Н": "н",
        "П": "п",
        "Р": "р",
        "Т": "т",
        "У": "у",
        "Ф": "ф",
        "Х": "х",
        "Ц": "ц",
        "Ш": "ш",
        "Ь": "ь",
        "Ы": "ы",
    }
    chars = []
    for index, char in enumerate(word):
        if index > 0 and char in replacements:
            chars.append(replacements[char])
        else:
            chars.append(char)
    normalized = "".join(chars)
    if force_lower:
        normalized = normalized.lower()
        normalized = re.sub(r"([аеёиоуыэюя])\1+", r"\1", normalized)
    return normalized


def fix_stressed_i_ocr(word: str) -> tuple[str, bool]:
    chars: list[str] = []
    changed = False
    source = list(word)
    index = 0
    while index < len(source):
        char = source[index]
        if char not in {"й", "Й"}:
            chars.append(char)
            index += 1
            continue
        if index == 0:
            chars.append(char)
            index += 1
            continue
        previous = source[index - 1]
        if previous in CONSONANTS:
            chars.append("и" if char == "й" else "И")
            if index + 1 < len(source) and source[index + 1] in {"и", "И"}:
                index += 2
            else:
                index += 1
            changed = True
            continue
        chars.append(char)
        index += 1
    fixed = "".join(chars)
    fixed = re.sub(r"иить\b", "ить", fixed)
    fixed = re.sub(r"ииться\b", "иться", fixed)
    fixed = re.sub(r"итть\b", "ить", fixed)
    fixed = re.sub(r"итться\b", "иться", fixed)
    fixed = re.sub(r"ийй\b", "ий", fixed)
    fixed = re.sub(r"ыйй\b", "ый", fixed)
    fixed = re.sub(r"ыый\b", "ый", fixed)
    fixed = re.sub(r"ойй(?=н)", "ой", fixed)
    fixed = re.sub(r"ойй\b", "ой", fixed)
    if fixed != "".join(chars):
        changed = True
    return fixed, changed


def risk_reasons(word: str) -> list[str]:
    reasons: list[str] = []
    if not CYRILLIC_WORD_RE.match(word):
        reasons.append("non_cyrillic_or_space")
    if any(char.isupper() for char in word[1:]):
        reasons.append("inner_uppercase")
    if len(word) > 24:
        reasons.append("very_long_headword")
    if not any(char in VOWELS for char in word):
        reasons.append("no_vowel")
    if CONSONANT_CLUSTER_RE.search(word):
        reasons.append("long_consonant_cluster")
    lower = word.lower()
    for index, char in enumerate(lower):
        if char != "й" or index == 0 or index + 1 >= len(lower):
            continue
        if word[index - 1] in CONSONANTS and word[index + 1] in CONSONANTS:
            reasons.append("й_before_consonant")
            break
    if re.search(r"[аеиоуыэюяё]й[аеиоуыэюяё]", lower):
        reasons.append("й_between_vowels")
    if re.search(r"(йист|йир|йич|нбом|нбм|тй|лйзм)", lower):
        reasons.append("known_ocr_pattern")
    return reasons


def score_reasons(reasons: list[str]) -> int:
    weights = {
        "non_cyrillic_or_space": 20,
        "inner_uppercase": 15,
        "very_long_headword": 20,
        "no_vowel": 30,
        "long_consonant_cluster": 20,
        "й_before_consonant": 10,
        "й_between_vowels": 8,
        "known_ocr_pattern": 18,
    }
    return sum(weights.get(reason, 0) for reason in reasons)


def suggest(row: dict[str, str], reasons: list[str]) -> tuple[str, str, str, str]:
    word = normalize_text(row.get("word", ""))
    meaning = normalize_text(row.get("meaning_zh", ""))
    if word in ACRONYMS:
        return word, "keep", "high", "recognized_acronym"
    if word in KNOWN_CORRECTIONS:
        suggested, confidence, basis = KNOWN_CORRECTIONS[word]
        if not suggested:
            return word, "reject_or_split", confidence, basis
        return suggested, "approve_correction", confidence, basis

    normalized = visual_normalize(word)
    if "very_long_headword" in reasons:
        return normalized, "reject_or_split", "low", "likely_phrase_or_sentence_not_single_word"
    i_fixed, i_changed = fix_stressed_i_ocr(normalized)
    if i_changed and CYRILLIC_WORD_RE.match(i_fixed):
        return i_fixed, "approve_correction", "medium", "stressed_i_ocr й_to_и_after_consonant"
    if normalized != word and CYRILLIC_WORD_RE.match(normalized):
        normalized_reasons = risk_reasons(normalized)
        blocking_reasons = {"very_long_headword", "no_vowel", "long_consonant_cluster", "non_cyrillic_or_space"}
        if not blocking_reasons.intersection(normalized_reasons):
            return normalized, "approve_correction", "medium", "visual_uppercase_noise_normalized"
        return normalized, "needs_review", "medium", "visual_uppercase_noise_normalized"

    if "no_vowel" in reasons:
        return word, "needs_review", "low", "no_vowel_in_headword"
    if reasons:
        return word, "needs_review", "low", "shape_risk_requires_manual_or_llm_review"
    return word, "keep", "high", "no_shape_risk_detected"


def audit_rows(rows: list[dict[str, str]], include_keep: bool = False) -> list[dict[str, str]]:
    audited: list[dict[str, str]] = []
    for row in rows:
        word = normalize_text(row.get("word", ""))
        reasons = risk_reasons(word)
        suggested_word, action, confidence, basis = suggest(row, reasons)
        if action == "keep" and not include_keep:
            continue
        out = {
            "source_file": row.get("source_file", ""),
            "source_page": row.get("source_page", ""),
            "block_index": row.get("block_index", ""),
            "current_word": word,
            "suggested_word": suggested_word,
            "suggested_meaning_zh": normalize_text(row.get("meaning_zh", "")),
            "action": action,
            "confidence": confidence,
            "risk_score": str(score_reasons(reasons)),
            "reasons": ";".join(reasons),
            "basis": basis,
            "original_word": row.get("original_word", ""),
            "part_of_speech": row.get("part_of_speech", ""),
            "raw_meaning_zh": row.get("raw_meaning_zh", ""),
            "raw_headword": row.get("raw_headword", ""),
            "raw_block": row.get("raw_block", ""),
        }
        audited.append(out)
    audited.sort(key=lambda item: (-int(item["risk_score"]), item["source_page"], item["block_index"]))
    return audited


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, str]]) -> dict[str, object]:
    action_counts: dict[str, int] = {}
    confidence_counts: dict[str, int] = {}
    for row in rows:
        action_counts[row["action"]] = action_counts.get(row["action"], 0) + 1
        confidence_counts[row["confidence"]] = confidence_counts.get(row["confidence"], 0) + 1
    return {
        "audit_rows": len(rows),
        "actions": action_counts,
        "confidence": confidence_counts,
        "top_examples": [
            {
                "word": row["current_word"],
                "suggested_word": row["suggested_word"],
                "action": row["action"],
                "reasons": row["reasons"],
            }
            for row in rows[:20]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit OCR risks in the simplified TEM-8 vocabulary sheet.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--include-keep", action="store_true")
    args = parser.parse_args()

    rows = read_csv(args.input)
    audited = audit_rows(rows, include_keep=args.include_keep)
    write_csv(args.output, audited)
    summary = summarize(audited)
    summary["input_rows"] = len(rows)
    summary["output"] = str(args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
