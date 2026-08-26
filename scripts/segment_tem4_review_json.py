from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

OPTION_KEY_MAP = {
    "A": "A", "А": "A", "B": "B", "В": "B", "C": "C", "С": "C",
    "D": "D", "Д": "D", "О": "D", "O": "D", "Р": "D", "р": "D",
}

YEAR_CONFIG: dict[int, dict[str, Any]] = {
    year: {
        "listening": (1, 15),
        "grammar": (16, 55),
        "culture": (56, 60),
        "cloze": (61, 70),
        "reading": (71, 90),
    }
    for year in (2017, 2018, 2019, 2021, 2022, 2023)
}
YEAR_CONFIG[2024] = {
    "listening": (1, 15),
    "grammar": (16, 65),
    "culture": (66, 70),
    "cloze": (71, 80),
    "reading": (81, 100),
}

# These are only the answer keys that were legible in the supplied matrices.
# Missing values intentionally remain blank for human review.
ANSWER_OVERRIDES: dict[int, dict[int, str]] = {
    2017: {
        1: "C", 2: "B", 3: "A", 4: "A", 5: "B", 6: "C", 7: "D", 8: "D", 9: "A", 10: "D",
        16: "C", 17: "A", 18: "B", 19: "A", 20: "C", 21: "D", 22: "B", 23: "C", 24: "B", 25: "C",
        26: "A", 27: "B", 28: "A", 29: "C", 30: "A", 31: "C", 32: "B", 33: "B", 34: "C", 35: "A", 36: "B", 37: "C", 38: "D", 39: "B", 40: "C",
        41: "B", 42: "A", 43: "C", 44: "D", 45: "A", 46: "D", 47: "B", 48: "C", 49: "B", 50: "A",
        51: "D", 52: "C", 53: "D", 54: "C", 55: "D", 56: "A", 57: "C", 58: "D", 59: "A", 60: "B",
        61: "A", 62: "C", 63: "D", 64: "B", 65: "C", 66: "B", 67: "B", 68: "C", 69: "C", 70: "D",
        71: "B", 72: "B", 73: "A", 74: "C", 75: "D", 76: "A", 77: "D", 78: "C", 79: "D", 80: "B",
        81: "D", 82: "A", 83: "A", 84: "C", 85: "C", 86: "A", 87: "C", 88: "B", 89: "C", 90: "C",
    },
    2018: {
        1: "C", 2: "A", 3: "B", 4: "D", 5: "C", 6: "D", 7: "C", 8: "A", 9: "A", 10: "D",
        11: "B", 12: "B", 13: "D", 14: "D", 15: "A", 16: "A", 17: "B", 18: "A", 19: "D", 20: "D",
        21: "A", 22: "D", 23: "B", 24: "D", 25: "A", 26: "B", 27: "D", 28: "A", 29: "A", 30: "D",
        31: "A", 32: "B", 33: "A", 36: "B", 37: "D", 38: "A", 39: "A", 40: "B", 41: "C", 42: "A",
        43: "B", 44: "D", 46: "A", 47: "D", 48: "C", 49: "B", 51: "A", 52: "B", 53: "C", 54: "B",
        56: "B", 58: "A", 59: "D", 61: "B", 62: "C", 63: "C", 64: "D", 65: "A", 66: "C", 67: "D",
        68: "D", 69: "D", 70: "A", 71: "D", 72: "B", 73: "C", 74: "B", 75: "A", 76: "A", 77: "D",
        78: "C", 79: "A", 80: "B", 81: "B", 82: "B", 83: "B", 84: "A", 85: "C",
    },
}


@dataclass
class QuestionChunk:
    number: int
    raw_text: str
    source_page: int | None


def normalize_option_key(value: str) -> str:
    return OPTION_KEY_MAP.get(value, value)


def normalize_lines(text: str) -> list[str]:
    return [line.strip() for line in text.replace("\ufeff", "").splitlines()]


def current_page(line: str) -> int | None:
    match = re.match(r"^--- Page (\d+)(?: \([^)]+\))? ---$", line)
    return int(match.group(1)) if match else None


def split_task_questions(section_text: str, first_number: int, last_number: int) -> list[QuestionChunk]:
    """Split listening items whose stems are introduced by `Задание n`."""
    chunks: list[QuestionChunk] = []
    current: int | None = None
    current_page_number: int | None = None
    active_page: int | None = None
    buffer: list[str] = []
    marker = re.compile(r"^\s*[^A-Za-zА-Яа-я0-9]{0,3}Зад\w*\s*(\d{1,3})\s*[.,]?(?:\s*(.*))?$", re.I)

    for line in normalize_lines(section_text):
        page = current_page(line)
        if page is not None:
            active_page = page
            continue
        match = marker.match(line)
        if not match:
            if current is not None:
                buffer.append(line)
            continue
        number = int(match.group(1))
        if not first_number <= number <= last_number:
            continue
        if current is not None:
            chunks.append(QuestionChunk(current, "\n".join(buffer).strip(), current_page_number))
        current = number
        current_page_number = active_page
        buffer = [match.group(2).strip()] if match.group(2) else []

    if current is not None:
        chunks.append(QuestionChunk(current, "\n".join(buffer).strip(), current_page_number))
    return chunks


def split_numbered_questions(section_text: str, first_number: int, last_number: int) -> list[QuestionChunk]:
    chunks: list[QuestionChunk] = []
    current: int | None = None
    current_page_number: int | None = None
    active_page: int | None = None
    buffer: list[str] = []
    question_start = re.compile(r"^\s*(?:Задание\s+)?(\d{1,3})(?:[.,)]|(?=\s|$))(?:\s*(.*))?$", re.I)

    for line in normalize_lines(section_text):
        page = current_page(line)
        if page is not None:
            active_page = page
            continue
        match: Any = question_start.match(line)
        expected = first_number if current is None else current + 1
        if match:
            candidate = int(match.group(1))
            if not (first_number <= candidate <= last_number and candidate == expected):
                match = None
        if not match and current is not None:
            expected = current + 1
            ocr_number = re.match(rf"^\s*{str(expected)[:1]}\s*[$#S]\.\s*(.*)$", line, re.I)
            if ocr_number:
                match = (expected, ocr_number.group(1))            # Recover only an unambiguous OCR number such as `3$.` for 38.
            fuzzy = re.match(
                rf"^\s*{str(expected)[:1]}\s*[^A-Za-zА-Яа-я0-9\s]{1,3}[.)]\s*(.*)$",
                line,
            )
            if not fuzzy:
                fuzzy = re.match(
                    rf"^\s*{str(expected)[:1]}\s+[^A-Za-zА-Яа-я0-9\s]{1,3}\s*(.*)$",
                    line,
                )
            if not fuzzy:
                fuzzy = re.match(
                    rf"^\s*{str(expected)[:1]}\s+.{1,3}(?:\s+(.*))?$",
                    line,
                )
            if fuzzy and first_number <= expected <= last_number:
                match = (expected, fuzzy.group(1))
        if match:
            number = int(match.group(1)) if hasattr(match, "group") else int(match[0])
            expected = first_number if current is None else current + 1
            if first_number <= number <= last_number and number == expected:
                if current is not None:
                    chunks.append(QuestionChunk(current, "\n".join(buffer).strip(), current_page_number))
                current = number
                current_page_number = active_page
                first_text = match.group(2) if hasattr(match, "group") else match[1]
                buffer = [first_text.strip()] if first_text else []
                continue
        if current is not None:
            buffer.append(line)

    if current is not None:
        chunks.append(QuestionChunk(current, "\n".join(buffer).strip(), current_page_number))
    return chunks


def extract_options(raw_text: str) -> tuple[str, list[dict[str, str]]]:
    marker = re.compile(r"(?:^|[\s`'|\\])([AАBВCСDДОOРр])[.)]\s*")
    text = " ".join(line for line in normalize_lines(raw_text) if line)
    matches = list(marker.finditer(text))
    if not matches:
        return " ".join(text.split()), []
    stem = " ".join(text[: matches[0].start()].split())
    options: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, match in enumerate(matches):
        key = normalize_option_key(match.group(1))
        if key in seen or key not in {"A", "B", "C", "D"}:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        options.append({"key": key, "text": " ".join(text[match.end():end].split())})
        seen.add(key)
    return stem, options


def answer_map(answer_text: str, year: int) -> dict[int, str]:
    answers = dict(ANSWER_OVERRIDES.get(year, {}))
    normalized = answer_text.translate(
        str.maketrans({"А": "A", "В": "B", "С": "C", "О": "D", "Д": "D", "Р": "D", "р": "D"})
    )
    lines = [line.strip() for line in normalized.splitlines()]
    pair_pattern = re.compile(r"(?<!\d)(\d{1,3})\s*[.)]?\s*([ABCD])(?=\s|$)")
    for line in lines:
        pairs = pair_pattern.findall(line)
        if len(pairs) < 5:
            continue
        for number, letter in pairs:
            answers.setdefault(int(number), letter)

    number_line = re.compile(r"^(\d{1,3})\s*[.)、]?$")
    letter_line = re.compile(r"^([ABCD])\s*[.)、]?$")
    index = 0
    while index < len(lines):
        numbers: list[int] = []
        cursor = index
        while cursor < len(lines):
            match = number_line.fullmatch(lines[cursor])
            if not match:
                break
            numbers.append(int(match.group(1)))
            cursor += 1
        if len(numbers) < 5:
            index += 1
            continue
        letters: list[str] = []
        letter_cursor = cursor
        while letter_cursor < len(lines) and len(letters) < len(numbers):
            match = letter_line.fullmatch(lines[letter_cursor])
            if not match:
                break
            letters.append(match.group(1))
            letter_cursor += 1
        if len(letters) == len(numbers):
            for number, letter in zip(numbers, letters):
                answers.setdefault(number, letter)
            index = letter_cursor
        else:
            index += 1
    return answers


def classify(number: int, config: dict[str, Any]) -> str | None:
    for name, (start, end) in config.items():
        if name == "cloze":
            continue
        if start <= number <= end:
            return f"{name}_choice"
    return None


def locate_reading_start(text: str, reading_start: int) -> int:
    # A cloze passage can contain a sentence beginning with "Чтение (71)".
    # Accept an independent section heading first, then a heading carrying the
    # reading score; only use the first question number as a last resort.
    heading = re.search(r"(?mi)^\s*(?:ЧТЕНИЕ|Чтение|阅读理解)\s*(?:\r?\n|$)", text)
    if heading:
        return heading.start()
    scored_heading = re.search(r"(?mi)^.*(?:ЧТЕНИЕ|Чтение|阅读理解).*20\s*балл", text)
    if scored_heading:
        return scored_heading.start()
    match = re.search(rf"(?m)^\s*{reading_start}(?:[.)]|\s)", text)
    return match.start() if match else len(text)

def locate_grammar_start(text: str) -> int:
    match = re.search(r"(?mi)^.*грамматика.*$", text)
    if match:
        return match.start()
    match = re.search(r"(?m)^\s*16(?:[.)]|\s)", text)
    return match.start() if match else 0
def split_passages(reading_text: str, reading_start: int, reading_end: int) -> list[tuple[str, str, list[QuestionChunk]]]:
    marker = re.compile(
        r"(?mi)^\s*(?:Текст\s*[1-5]?|文章\s*[1-5]?|MH\s*[1-5]?|MHA|MHI|MHE|ME\s*[1-5]?|ХЫ\s*[1-5]?|ХМ\s*[1-5]?|T\s*[1-5])\s*$"
    )
    matches = list(marker.finditer(reading_text))
    passages: list[tuple[str, str, list[QuestionChunk]]] = []
    total_questions = reading_end - reading_start + 1
    passage_count = max(1, (total_questions + 5 - 1) // 5)
    segments: list[tuple[int, str]] = []
    # Some scans omit the first `Текст 1` label. Keep the prefix as article 1
    # only when it contains the first reading question.
    if matches:
        prefix = reading_text[:matches[0].start()]
        if re.search(rf"(?m)^\s*(?:{reading_start}[.)]?|Задание\s+{reading_start})\s*", prefix, re.I):
            segments.append((1, prefix))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(reading_text)
            segments.append((len(segments) + 1, reading_text[match.end():end]))
    else:
        segments.append((1, reading_text))

    for index, (passage_number, segment) in enumerate(segments[:passage_count]):
        expected_start = reading_start + index * 5
        expected_end = min(expected_start + 4, reading_end)
        segment = segment.strip()
        question_position = re.search(rf"(?m)^\s*(?:{expected_start}[.)]?|Задание\s+{expected_start})\s*", segment, re.I)
        if not question_position:
            continue
        body = segment[:question_position.start()].strip()
        question_text = segment[question_position.start():]
        chunks = split_numbered_questions(question_text, expected_start, expected_end)
        passages.append((f"文章{passage_number}", body, chunks))
    return passages

def make_question(
    chunk: QuestionChunk,
    stem: str,
    options: list[dict[str, str]],
    answer: str | None,
    qtype: str,
    year: int,
    source_file: str,
    passage: dict[str, str] | None,
) -> dict[str, Any]:
    return {
        "source_year": year,
        "exam_system": "TEM4_RU",
        "level": "TEM4",
        "section": qtype,
        "question_type": qtype,
        "source_question_number": str(chunk.number),
        "stem": stem,
        "options": options,
        "correct_answer": answer,
        "passage": passage,
        "source_page": chunk.source_page,
        "raw_text": chunk.raw_text,
        "review_status": "needs_review",
        "source_usage": "practice",
        "content_origin": "past_exam_original",
        "source_label": f"{year} 年俄语专四真题",
        "requires_source_label": True,
        "eligible_for_quiz_after_approval": True,
        "source_file": source_file,
    }


def build_questions(text: str, answers: dict[int, str], year: int, source_file: str) -> list[dict[str, Any]]:
    config = YEAR_CONFIG[year]
    questions: list[dict[str, Any]] = []
    reading_start, reading_end = config["reading"]
    reading_position = locate_reading_start(text, reading_start)
    pre_reading = text[:reading_position]

    # Listening uses task markers, which are often OCR-corrupted slightly.
    for chunk in split_task_questions(pre_reading, 1, 15):
        stem, options = extract_options(chunk.raw_text)
        questions.append(make_question(chunk, stem, options, answers.get(chunk.number), "listening_choice", year, source_file, None))

    grammar_position = locate_grammar_start(pre_reading)
    grammar_text = pre_reading[grammar_position:]
    supported_end = config["culture"][1]
    for chunk in split_numbered_questions(grammar_text, config["grammar"][0], supported_end):
        qtype = classify(chunk.number, config)
        if qtype is None:
            continue
        stem, options = extract_options(chunk.raw_text)
        questions.append(make_question(chunk, stem, options, answers.get(chunk.number), qtype, year, source_file, None))

    reading_text = text[reading_position:]
    for title, body, chunks in split_passages(reading_text, reading_start, reading_end):
        passage = {"title": title, "body": body}
        for chunk in chunks:
            stem, options = extract_options(chunk.raw_text)
            questions.append(make_question(chunk, stem, options, answers.get(chunk.number), "reading_choice", year, source_file, passage))

    questions.sort(key=lambda item: int(item["source_question_number"]))
    return questions


def summarize(questions: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for question in questions:
        qtype = question["question_type"]
        counts[qtype] = counts.get(qtype, 0) + 1
    missing_options = [q["source_question_number"] for q in questions if len(q["options"]) != 4]
    missing_answers = [q["source_question_number"] for q in questions if not q["correct_answer"]]
    expected = sum(end - start + 1 for name, (start, end) in config.items() if name != "cloze")
    return {
        "total_questions": len(questions),
        "expected_supported_questions": expected,
        "counts_by_type": counts,
        "missing_options": missing_options,
        "missing_answers": missing_answers,
        "cloze_excluded": list(range(config["cloze"][0], config["cloze"][1] + 1)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Segment TEM4 text into an isolated review JSON.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--year", type=int, required=True, choices=sorted(YEAR_CONFIG))
    parser.add_argument("--answers-input", type=Path)
    args = parser.parse_args()
    text = args.input.read_text(encoding="utf-8", errors="replace")
    answer_text = args.answers_input.read_text(encoding="utf-8", errors="replace") if args.answers_input else text
    answers = answer_map(answer_text, args.year)
    questions = build_questions(text, answers, args.year, str(args.input).replace("\\", "/"))
    config = YEAR_CONFIG[args.year]
    payload = {
        "source_file": str(args.input).replace("\\", "/"),
        "answers_source_file": str(args.answers_input).replace("\\", "/") if args.answers_input else None,
        "source_year": args.year,
        "exam_system": "TEM4_RU",
        "level": "TEM4",
        "review_status": "needs_review",
        "source_usage": "practice",
        "content_origin": "past_exam_original",
        "source_label": f"{args.year} 年俄语专四真题",
        "requires_source_label": True,
        "eligible_for_quiz_after_approval": True,
        "summary": summarize(questions, config),
        "questions": questions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    print(f"Wrote review JSON: {args.output}")


if __name__ == "__main__":
    main()












