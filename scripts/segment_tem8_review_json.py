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
    "O": "D",
    "О": "D",
    "0": "D",
    "2": "D",
    "Р": "D",
    "р": "D",
    "а": "D",
}


ANSWER_OVERRIDES = {
    2017: {
        16: "C",
        21: "D",
        29: "D",
        30: "A",
        31: "C",
        34: "D",
        38: "C",
        39: "D",
    },
    2018: {
        16: "B",
        21: "B",
        25: "D",
        29: "D",
        32: "D",
        39: "D",
        42: "D",
        45: "C",
        54: "D",
    },
    2024: {
        16: "C",
        17: "A",
        18: "B",
        19: "B",
        20: "A",
        21: "D",
        22: "C",
        23: "B",
        24: "C",
        25: "D",
        26: "A",
        27: "C",
        28: "B",
        29: "C",
        30: "B",
        31: "A",
        32: "D",
        33: "B",
        34: "A",
        35: "B",
        36: "D",
        37: "C",
        38: "D",
        39: "B",
        40: "C",
        41: "A",
        42: "D",
        43: "B",
        44: "C",
        45: "A",
        56: "B",
        57: "A",
        58: "B",
        59: "D",
        60: "C",
        61: "C",
        62: "D",
        63: "A",
        64: "D",
        65: "C",
        66: "B",
        67: "A",
        68: "B",
        69: "A",
        70: "B",
        71: "A",
        72: "A",
        73: "B",
        74: "C",
        75: "D",
    },
}


OPTION_OVERRIDES = {
    2017: {
        25: {
            "A": "внесет",
            "B": "несет",
            "C": "внесут",
            "D": "несут",
        },
        26: {
            "A": "на сотрудничестве",
            "B": "сотрудничеством",
            "C": "в сотрудничестве",
            "D": "сотрудничество",
        },
        36: {
            "A": "А. А. Фет",
            "B": "М. И. Цветаева",
            "C": "С. А. Есенин",
            "D": "А. А. Ахматова",
        },
        37: {
            "A": "Евгений и Татьяна",
            "B": "Юрий и Лара",
            "C": "Родион и Сонечка",
            "D": "Андрей и Наташа",
        },
        38: {
            "A": "«Деревня»",
            "B": "«Митина любовь»",
            "C": "«Темные аллеи»",
            "D": "«Окаянные дни»",
        },
    },
    2018: {
        26: {
            "A": "уделялось",
            "B": "отводилось",
            "C": "оставалось",
            "D": "придавалось",
        },
        27: {
            "A": "влияет",
            "B": "сказывается",
            "C": "отражает",
            "D": "воздействует",
        },
        37: {
            "A": "классицизм",
            "B": "сентиментализм",
            "C": "романтизм",
            "D": "реализм",
        },
        38: {
            "A": "Евгений Базаров",
            "B": "Петр Гринев",
            "C": "Григорий Мелехов",
            "D": "Андрей Соколов",
        },
    },
}


@dataclass
class QuestionChunk:
    number: int
    raw_text: str
    source_page: int | None


def normalize_option_key(value: str) -> str:
    return OPTION_KEY_MAP.get(value, value)


def apply_option_override(source_year: int, number: int, options: list[dict]) -> list[dict]:
    override = OPTION_OVERRIDES.get(source_year, {}).get(number)
    if not override:
        return options
    return [{"key": key, "text": text} for key, text in override.items()]


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


def section_between_question_numbers(text: str, start_number: int, end_number: int) -> str:
    start_match = re.search(rf"(?m)^[^\wА-Яа-яA-Za-z]*{start_number}[\.)]\s+", text)
    end_match = re.search(rf"(?m)^[^\wА-Яа-яA-Za-z]*{end_number}[\.)]\s+", text)
    if not start_match:
        return ""
    end_index = end_match.start() if end_match else len(text)
    return text[start_match.start() : end_index]


def reading_section_text(text: str) -> str:
    section = section_between(text, "阅读理解", "翻译")
    if section:
        return section

    section = section_between(text, "Чтение", "Переведите")
    if section:
        return section

    first_question = re.search(r"(?m)^\s*46[\.)]\s+", text)
    if not first_question:
        return ""

    start = text.rfind("Текст", 0, first_question.start())
    if start < 0:
        start = text.rfind("екст", 0, first_question.start())
    if start < 0:
        start = first_question.start()

    end_match = re.search(r"(?m)^\s*1[\.)]\s+Переведите", text[first_question.start() :])
    end = first_question.start() + end_match.start() if end_match else len(text)
    return text[start:end]


def reading_number_range(source_year: int) -> tuple[int, int]:
    if source_year == 2024:
        return 56, 75
    return 46, 65


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

    question_start = re.compile(r"^[^\wА-Яа-яA-Za-z]*(\d{1,2})[\.)]?(?:\s+(.*))?$")

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
    option_marker = re.compile(r"(?:^|[\s`'|\\])([AАBВCСDДОO02Рра])[\.)]\s*")
    normalized_text = "\n".join(line for line in normalize_lines(raw_text) if line)
    matches = list(option_marker.finditer(normalized_text))
    if matches:
        stem = " ".join(normalized_text[: matches[0].start()].split())
        options: list[dict] = []
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized_text)
            options.append(
                {
                    "key": normalize_option_key(match.group(1)),
                    "text": " ".join(normalized_text[match.end() : end].split()),
                }
            )
        deduped_options: list[dict] = []
        seen_keys: set[str] = set()
        for option in options:
            if option["key"] in seen_keys:
                continue
            seen_keys.add(option["key"])
            deduped_options.append(option)
        return stem, deduped_options

    return " ".join(normalized_text.split()), []


def classify_comprehensive_question(number: int) -> str:
    if 16 <= number <= 32:
        return "grammar_choice"
    if 33 <= number <= 39:
        return "literature_choice"
    return "culture_choice"


def parse_answers(text: str) -> dict[int, str]:
    answer_section = section_between(text, "答案", "翻译")
    if not answer_section:
        answer_section = text
    tokens = [
        line.strip()
        for line in answer_section.splitlines()
        if re.match(r"^\d{1,2}$", line.strip()) or re.match(r"^[AАBВCСDДОO02]$", line.strip())
    ]

    answers: dict[int, str] = {}
    for number, answer in re.findall(r"(?<!\d)(\d{1,2})\.\s*([AАBВCСDДОO02])(?:\b|$)", answer_section):
        answers[int(number)] = normalize_option_key(answer)

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

    for number in range(16, 46):
        block_start = re.search(rf"(?m)^\s*{number}\.\s+", answer_section)
        if not block_start:
            continue
        next_start = re.search(rf"(?m)^\s*{number + 1}\.\s+", answer_section[block_start.end() :])
        block_end = block_start.end() + next_start.start() if next_start else len(answer_section)
        block = answer_section[block_start.end() : block_end]
        match = re.search(r"(?m)^\[[^\]\n]*\]\s*([AАBВCСDДОO02])(?:\s|$)", block)
        if not match:
            match = re.search(r"(?m)^\[[^\n]*\s+([AАBВCСDДОO02])(?:\s|$)", block)
        if match:
            answers[number] = normalize_option_key(match.group(1))

    return answers


def parse_comprehensive_questions(text: str, answers: dict[int, str], source_year: int) -> list[dict]:
    section = section_between(text, "综合知识", "阅读理解")
    if not section:
        section = section_between_question_numbers(text, 16, 46)
        reading_heading = re.search(r"(?mi)^.*Чтение.*$", section)
        if reading_heading:
            section = section[: reading_heading.start()]
        cloze_heading = re.search(r"(?mi)^.*ЗАПОЛНЕНИЕ ПРОПУСКОВ.*$", section)
        if cloze_heading:
            section = section[: cloze_heading.start()]
    chunks = split_numbered_questions(section, 16, 45, first_number=16)
    questions: list[dict] = []

    for chunk in chunks:
        stem, options = extract_options(chunk.raw_text)
        options = apply_option_override(source_year, chunk.number, options)
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
                "source_usage": "practice",
                "content_origin": "past_exam_original",
                "source_label": f"{source_year} 年俄语专八真题",
                "requires_source_label": True,
                "eligible_for_quiz_after_approval": True,
            }
        )

    return questions


def split_reading_passages(reading_section: str) -> list[tuple[str, str]]:
    marker_pattern = re.compile(r"(?:文章|Текст|текст|екст)")
    offset = 0
    matches: list[tuple[int, int, str | None]] = []
    for line in reading_section.splitlines(keepends=True):
        stripped = line.strip()
        marker_number: str | None = None
        is_marker = False
        if len(stripped) <= 50 and marker_pattern.search(stripped):
            is_marker = True
            number_match = re.search(r"([1-5])", stripped)
            marker_number = number_match.group(1) if number_match else None
        elif re.match(r"^[\\|]\s*([1-5])\s+\S{2,10}\s*$", stripped):
            is_marker = True
            marker_number = re.match(r"^[\\|]\s*([1-5])", stripped).group(1)
        if is_marker:
            matches.append((offset, offset + len(line), marker_number))
        offset += len(line)

    passages: list[tuple[str, str]] = []

    for index, match in enumerate(matches):
        passage_number = match[2] or str(index + 1)
        title = f"文章{passage_number}"
        start = match[1]
        end = matches[index + 1][0] if index + 1 < len(matches) else len(reading_section)
        passages.append((title, reading_section[start:end].strip()))

    return passages


def first_question_position(passage_text: str, expected_start: int) -> int | None:
    match = re.search(rf"(?m)^\s*{expected_start}[\.)]?(?:\s+|$)", passage_text)
    return match.start() if match else None


def parse_reading_questions(text: str, answers: dict[int, str], source_year: int) -> list[dict]:
    reading_section = reading_section_text(text)
    questions: list[dict] = []
    reading_start, reading_end = reading_number_range(source_year)

    for passage_title, passage_text in split_reading_passages(reading_section):
        passage_number_match = re.search(r"(\d+)", passage_title)
        if not passage_number_match:
            continue
        passage_number = int(passage_number_match.group(1))
        expected_start = reading_start + (passage_number - 1) * 4
        expected_end = min(expected_start + 3, reading_end)

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
            options = apply_option_override(source_year, chunk.number, options)
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
                    "source_usage": "practice",
                    "content_origin": "past_exam_original",
                    "source_label": f"{source_year} 年俄语专八真题",
                    "requires_source_label": True,
                    "eligible_for_quiz_after_approval": True,
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
    parser.add_argument(
        "--answers-input",
        type=Path,
        help="Optional extracted answers text when questions and answers are stored in separate PDFs.",
    )
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8", errors="replace")
    answers_text = (
        args.answers_input.read_text(encoding="utf-8", errors="replace")
        if args.answers_input
        else text
    )
    answers = parse_answers(answers_text)
    for number, answer in ANSWER_OVERRIDES.get(args.year, {}).items():
        answers.setdefault(number, answer)
    questions = parse_comprehensive_questions(text, answers, args.year)
    questions.extend(parse_reading_questions(text, answers, args.year))

    payload = {
        "source_file": str(args.input).replace("\\", "/"),
        "answers_source_file": str(args.answers_input).replace("\\", "/") if args.answers_input else None,
        "source_year": args.year,
        "review_status": "needs_review",
        "source_usage": "practice",
        "content_origin": "past_exam_original",
        "source_label": f"{args.year} 年俄语专八真题",
        "requires_source_label": True,
        "eligible_for_quiz_after_approval": True,
        "summary": summarize(questions, answers),
        "questions": questions,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    print(f"Wrote review JSON: {args.output}")


if __name__ == "__main__":
    main()
