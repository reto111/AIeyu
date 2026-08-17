from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


OPTION_KEY_MAP = {
    "A": "A",
    "А": "A",
    "B": "B",
    "В": "B",
    "C": "C",
    "С": "C",
    "D": "D",
    "Д": "D",
}


@dataclass
class QuestionChunk:
    number: int
    raw_text: str
    source_page: int | None


def normalize_option_key(value: str) -> str:
    return OPTION_KEY_MAP.get(value, value)


def normalize_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue
        lines.append(line)
    return lines


def strip_page_marker(line: str) -> bool:
    return bool(re.match(r"^--- Page \d+ \([^)]+\) ---$", line))


def section_between(text: str, start: str, end: str) -> str:
    start_index = text.find(start)
    if start_index < 0:
        return ""
    start_index += len(start)
    end_index = text.find(end, start_index)
    if end_index < 0:
        return text[start_index:]
    return text[start_index:end_index]


def current_page_from_marker(line: str) -> int | None:
    match = re.match(r"^--- Page (\d+) \([^)]+\) ---$", line)
    if not match:
        return None
    return int(match.group(1))


def split_numbered_questions(
    section_text: str,
    min_number: int,
    max_number: int,
    first_number: int | None = None,
) -> list[QuestionChunk]:
    chunks: list[QuestionChunk] = []
    current_number: int | None = None
    current_page: int | None = None
    active_page: int | None = None
    buffer: list[str] = []

    question_start = re.compile(r"^(\d{1,2})(?:\s+(.*))?$")

    for line in normalize_lines(section_text):
        page_number = current_page_from_marker(line)
        if page_number is not None:
            active_page = page_number
            continue

        match = question_start.match(line)
        if match:
            number = int(match.group(1))
            rest = (match.group(2) or "").strip()
            expected_number = first_number if current_number is None else current_number + 1
            starts_valid_sequence = current_number is None and first_number is None
            follows_sequence = expected_number is not None and number == expected_number
            if min_number <= number <= max_number and (starts_valid_sequence or follows_sequence):
                if current_number is not None:
                    chunks.append(
                        QuestionChunk(
                            number=current_number,
                            raw_text="\n".join(buffer).strip(),
                            source_page=current_page,
                        )
                    )
                current_number = number
                current_page = active_page
                buffer = [rest] if rest else []
                continue

        if current_number is not None and not strip_page_marker(line):
            buffer.append(line)

    if current_number is not None:
        chunks.append(
            QuestionChunk(
                number=current_number,
                raw_text="\n".join(buffer).strip(),
                source_page=current_page,
            )
        )

    return chunks


def extract_options(raw_text: str) -> tuple[str, list[dict]]:
    option_marker = re.compile(r"^([AАBВCСDД])[\.)]\s*(.*)$")
    stem_lines: list[str] = []
    options: list[dict] = []
    current_option: dict | None = None

    for line in normalize_lines(raw_text):
        if not line:
            continue

        match = option_marker.match(line)
        if match:
            current_option = {
                "key": normalize_option_key(match.group(1)),
                "text": match.group(2).strip(),
            }
            options.append(current_option)
            continue

        if current_option is None:
            stem_lines.append(line)
        else:
            current_option["text"] = (current_option["text"] + " " + line).strip()

    stem = " ".join(stem_lines).strip()
    return stem, options


def classify_comprehensive_question(number: int) -> str:
    if 16 <= number <= 32:
        return "grammar_choice"
    if 33 <= number <= 39:
        return "literature_choice"
    return "culture_choice"


def parse_answers(text: str) -> dict[int, str]:
    answer_section = section_between(text, "答案", "翻译")
    tokens = [
        line.strip()
        for line in answer_section.splitlines()
        if re.match(r"^\d{1,2}$", line.strip()) or re.match(r"^[AАBВCСDД]$", line.strip())
    ]

    answers: dict[int, str] = {}
    index = 0
    while index < len(tokens):
        numbers: list[int] = []
        while index < len(tokens) and tokens[index].isdigit():
            numbers.append(int(tokens[index]))
            index += 1

        letters: list[str] = []
        while index < len(tokens) and not tokens[index].isdigit():
            letters.append(normalize_option_key(tokens[index]))
            index += 1
            if len(letters) == len(numbers):
                break

        for number, answer in zip(numbers, letters):
            answers[number] = answer

    return answers


def parse_comprehensive_questions(text: str, answers: dict[int, str], source_year: int) -> list[dict]:
    section = section_between(text, "综合知识", "阅读理解")
    chunks = split_numbered_questions(section, 16, 45, first_number=16)
    questions: list[dict] = []

    for chunk in chunks:
        stem, options = extract_options(chunk.raw_text)
        questions.append(
            {
                "source_year": source_year,
                "exam_system": "TEM8_RU",
                "level": "TEM8",
                "section": "综合知识",
                "question_type": classify_comprehensive_question(chunk.number),
                "source_question_number": str(chunk.number),
                "stem": stem,
                "options": options,
                "correct_answer": answers.get(chunk.number),
                "passage": None,
                "source_page": chunk.source_page,
                "raw_text": chunk.raw_text,
                "review_status": "needs_review",
            }
        )

    return questions


def split_reading_passages(reading_section: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"(?m)^文章(\d+)\s*$")
    matches = list(pattern.finditer(reading_section))
    passages: list[tuple[str, str]] = []

    for index, match in enumerate(matches):
        title = f"文章{match.group(1)}"
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(reading_section)
        passages.append((title, reading_section[start:end].strip()))

    return passages


def first_question_position(passage_text: str, expected_start: int) -> int | None:
    match = re.search(rf"(?m)^{expected_start}(?:\s+|$)", passage_text)
    return match.start() if match else None


def parse_reading_questions(text: str, answers: dict[int, str], source_year: int) -> list[dict]:
    reading_section = section_between(text, "阅读理解", "翻译")
    questions: list[dict] = []

    for passage_title, passage_text in split_reading_passages(reading_section):
        passage_number_match = re.search(r"(\d+)", passage_title)
        if not passage_number_match:
            continue
        passage_number = int(passage_number_match.group(1))
        expected_start = 46 + (passage_number - 1) * 4
        expected_end = min(expected_start + 3, 65)

        question_start = first_question_position(passage_text, expected_start)
        if question_start is None:
            continue

        passage_body = passage_text[:question_start].strip()
        question_text = passage_text[question_start:].strip()
        chunks = split_numbered_questions(
            question_text,
            expected_start,
            expected_end,
            first_number=expected_start,
        )

        for chunk in chunks:
            stem, options = extract_options(chunk.raw_text)
            questions.append(
                {
                    "source_year": source_year,
                    "exam_system": "TEM8_RU",
                    "level": "TEM8",
                    "section": "阅读理解",
                    "question_type": "reading_choice",
                    "source_question_number": str(chunk.number),
                    "stem": stem,
                    "options": options,
                    "correct_answer": answers.get(chunk.number),
                    "passage": {
                        "title": passage_title,
                        "body": passage_body,
                    },
                    "source_page": chunk.source_page,
                    "raw_text": chunk.raw_text,
                    "review_status": "needs_review",
                }
            )

    return questions


def summarize(questions: list[dict], answers: dict[int, str]) -> dict:
    missing_options = [
        item["source_question_number"]
        for item in questions
        if len(item["options"]) != 4
    ]
    missing_answers = [
        item["source_question_number"]
        for item in questions
        if not item["correct_answer"]
    ]

    counts_by_type: dict[str, int] = {}
    for item in questions:
        counts_by_type[item["question_type"]] = counts_by_type.get(item["question_type"], 0) + 1

    return {
        "total_questions": len(questions),
        "counts_by_type": counts_by_type,
        "answers_found": len(answers),
        "missing_options": missing_options,
        "missing_answers": missing_answers,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Segment TEM8 extracted text into review JSON.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8", errors="replace")
    answers = parse_answers(text)
    questions = parse_comprehensive_questions(text, answers, args.year)
    questions.extend(parse_reading_questions(text, answers, args.year))

    payload = {
        "source_file": str(args.input).replace("\\", "/"),
        "source_year": args.year,
        "review_status": "needs_review",
        "summary": summarize(questions, answers),
        "questions": questions,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    print(f"Wrote review JSON: {args.output}")


if __name__ == "__main__":
    main()
