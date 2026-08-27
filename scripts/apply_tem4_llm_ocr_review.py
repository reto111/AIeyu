from __future__ import annotations

import argparse
import csv
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
CLEAN_JSON = ROOT / "data" / "processed" / "tem4_review_clean" / "tem4_russian_2024_review.json"
CHECKED_JSON = ROOT / "data" / "processed" / "structured" / "tem4" / "tem4_russian_2024_review_llm_checked.json"
AUDIT_CSV = ROOT / "data" / "processed" / "question_quality" / "tem4" / "tem4_2024_llm_ocr_audit.csv"

# Conservative local-LLM decisions. Stems and passage bodies are not replaced
# because the clean OCR is not uniformly better than the original OCR.
# Question 3 is listening and is intentionally absent from the question DB.
# Keep listening corrections in the separate reference export only.
OPTION_REPLACEMENTS = {26, 40}
STEM_REPLACEMENTS = {
    16: "Нет счастья _____, чем чувствовать, что люди любят тебя и радуются твоему присутствию.",
    17: "Мимо нас быстро проехала машина скорой помощи, она _____ больного в больницу.",
    18: "Известный писатель Александр Куприн умеет объяснять читателю даже самые сложные вещи _____.",
    19: "Благодаря развитию современной техники учёные могут определить время наводнения _____ до его начала.",
    20: "Музыкальная радиопрограмма «Берёза» обычно длится _____ с полудня до двух.",
    21: "Молодость хороша _____ она имеет будущее.",
    22: "Этот вопрос будет _____ правительствами разных стран.",
    23: "_____ не было Солнца, не было бы и жизни на Земле.",
    24: "Преподаватель сказал нам, _____ завтра мы пришли на консультацию в четыре часа.",
    25: "Ольга уговорила брата не _____ о случившемся родителям.",
    26: "Этой работой должен заниматься тот, _____ есть большой опыт.",
    27: "Учёные утверждают, что даже очень робкий человек, если он поёт, чувствует себя _____.",
    28: "Дом старый, но в окнах горит свет, значит, там живёт _____.",
    29: "_____ весна наступила месяц назад, везде по-прежнему лежит снег.",
    30: "_____ мы вошли в лес, сразу стало прохладно, и летний день остался позади.",
    31: "Нельзя передать музыку словами, _____ был богат наш язык.",
    32: "_____ громко разговаривать во время спектакля.",
    33: "_____ на каникулы, студенты должны сдать книги в библиотеку.",
    34: "Даже на этой старой чёрно-белой фотографии было заметно, как глаза бабушки сверкали _____ счастья.",
    35: "Хорошо иметь друзей, на _____ помощь всегда можно рассчитывать.",
    36: "Знания бесконечны, поэтому человеку всегда _____ учиться.",
    37: "Все прохожие повернулись в ту сторону, _____ раздались громкие звуки.",
    38: "Семён всё лето _____ над новой книгой, иногда не выходил из дома.",
    39: "Человек должен поступать так, _____ требуют общепринятые нормы поведения.",
    40: "Фильм посвящён _____ из самых ярких страниц в истории Олимпиады.",
    41: "Несколько часов стоял густой туман, _____ мы не смогли вовремя выехать.",
    42: "Мы с Николаем стали редко встречаться _____ он перешёл на другую работу.",
    43: "Данные, _____ с космической станции, позволяют судить о характере поверхности Луны.",
    44: "Природа Урала так красива, _____ туристы приезжают сюда и зимой, и летом.",
    45: "Родители должны помочь ребёнку понять, что забота _____ приносит радость.",
    46: "Студенческий спектакль был таким интересным, _____ играли настоящие артисты.",
    47: "Солнце заглянуло в окно, _____ в комнате стало светло.",
    48: "На этой горе люди часто находили красивые зелёные камни, _____ они делали прекрасные вазы.",
    49: "Хирургу удалось вернуть зрение человеку, _____ 20 лет.",
    50: "Новую оперу горячо _____ в телепередачах, на страницах газет и журналов и, конечно, в Интернете.",
    51: "Описывая героев своих произведений, Иван Бунин всегда внимателен _____.",
    52: "Новая эпоха требует _____ особой силы и умения.",
    53: "Иногда отказывать человеку _____ очень трудно, даже если это необходимо.",
    54: "Важно хвалить себя _____ каждый маленький шаг на пути к достижению цели.",
    55: "Готовясь _____, мы покупаем подарки своим родным и близким.",
    56: "Чтение хороших книг напоминает _____ с величайшими людьми.",
    57: "Надо распределять время так, чтобы _____ хватало и на учёбу, и на отдых.",
    58: "В будущем роботы смогут _____ людей при выполнении опасных и вредных работ.",
    59: "Если родители берут ребёнка _____, то он чувствует их заботу и любовь.",
    60: "Борис уже собирался выйти из дома, но его _____ телефонный звонок.",
    61: "Алексей так сильно увлёкся чтением, что _____ свою остановку.",
    62: "У Веры плохое зрение. Она начала _____ очки в восемь лет.",
    63: "Важно, чтобы было хорошо и радостно всем, а _____ тебе.",
    64: "Долгое обсуждение _____ нас к выводу, что этот вопрос нельзя разрешить сразу.",
    65: "Чтобы спрятаться _____, ребята быстро зашли в кафе, которое было рядом.",
    66: "Если нам нужно написать деловое письмо незнакомому человеку по имени Михаил Степанович Иванов, вы можете начать своё письмо с обращения «_____.»",
    67: "Династия Романовых находилась у власти в России _____.",
    68: "Первая российская революция началась 22 января _____ года.",
    69: "12 апреля 2023 года исполнилось 200 лет со дня рождения _____, автора пьесы «Гроза».",
    70: "_____ не является членом «Могучей кучки».",
}
ANSWER_REPLACEMENTS = {
    18: "D", 20: "D", 28: "A", 37: "D", 42: "A", 45: "D", 51: "A", 53: "D", 57: "A",
    66: "D", 67: "C", 68: "C", 69: "B", 70: "A", 86: "D",
}
OPTION_TEXT_REPLACEMENTS = {
    31: {"A": "как", "B": "какой ни", "C": "как бы ни", "D": "какой бы ни"},
    26: {"A": "для кого", "B": "кто", "C": "у кого", "D": "кому"},
    37: {"A": "что", "B": "куда", "C": "какие", "D": "откуда"},
    39: {"A": "как", "B": "что", "C": "какие", "D": "будто"},
    40: {"D": "одних"},
    42: {"A": "с тех пор"},
    45: {"A": "за других", "B": "к другим", "C": "с другими", "D": "о других"},
    51: {"A": "к деталям"},
    57: {"A": "его"},
    62: {"A": "вести", "B": "нести", "C": "водить", "D": "носить"},
    63: {"A": "одному", "B": "единому", "C": "единственному", "D": "отдельному"},
    65: {"A": "под дождь", "B": "к дождю", "C": "из дождя", "D": "от дождя"},
    67: {"A": "196 лет"},
    50: {"A": "обсуждает", "B": "обсуждается", "C": "обсуждают", "D": "обсуждаются"},
    36: {"D": "нечему"},
    46: {"B": "каким бы"},
    56: {"D": "на беседу"},
    70: {"D": "М.П. Мусоргский"},
}


def load_clean_questions(path: Path) -> dict[int, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {int(item["source_question_number"]): item for item in payload["questions"]}


def find_question(conn: sqlite3.Connection, number: int) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT q.id, q.source_question_number, q.correct_answer, q.review_status
        FROM questions q
        JOIN exam_systems es ON es.id = q.exam_system_id
        WHERE es.code = 'TEM4_RU'
          AND q.source_year = 2024
          AND q.source_question_number = ?
        """,
        (str(number),),
    ).fetchone()
    if row is None:
        raise ValueError(f"Missing TEM4 2024 question {number}.")
    return row


def apply(
    db_path: Path,
    clean_json: Path,
    checked_json: Path,
    audit_csv: Path,
    dry_run: bool,
) -> dict[str, Any]:
    clean = load_clean_questions(clean_json)
    backup_path = db_path.parent.parent / "data" / "processed" / "backups" / (
        "russian_ai_tutor_before_tem4_llm_ocr_review_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".sqlite"
    )
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(db_path, backup_path)

    applied: list[int] = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        all_numbers = OPTION_REPLACEMENTS | set(ANSWER_REPLACEMENTS) | set(STEM_REPLACEMENTS) | set(OPTION_TEXT_REPLACEMENTS)
        for number in sorted(all_numbers):
            row = find_question(conn, number)
            qid = int(row["id"])
            item = clean[number]
            changed_fields: list[str] = []
            if number in OPTION_REPLACEMENTS:
                conn.execute("DELETE FROM question_options WHERE question_id = ?", (qid,))
                for sort_order, option in enumerate(item.get("options") or []):
                    conn.execute(
                        """
                        INSERT INTO question_options
                          (question_id, option_key, option_text, sort_order)
                        VALUES (?, ?, ?, ?)
                        """,
                        (qid, option["key"], option.get("text") or "", sort_order),
                    )
                changed_fields.append("options")
            if number in OPTION_TEXT_REPLACEMENTS:
                for key, text in OPTION_TEXT_REPLACEMENTS[number].items():
                    existing = conn.execute(
                        "SELECT id FROM question_options WHERE question_id = ? AND option_key = ?",
                        (qid, key),
                    ).fetchone()
                    if existing:
                        conn.execute(
                            "UPDATE question_options SET option_text = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (text, int(existing[0])),
                        )
                    else:
                        conn.execute(
                            "INSERT INTO question_options (question_id, option_key, option_text, sort_order) VALUES (?, ?, ?, ?)",
                            (qid, key, text, ord(key) - ord("A")),
                        )
                changed_fields.append("option_text")
            if number in STEM_REPLACEMENTS:
                conn.execute(
                    "UPDATE questions SET stem = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (STEM_REPLACEMENTS[number], qid),
                )
                changed_fields.append("stem")
            if number in ANSWER_REPLACEMENTS:
                conn.execute(
                    "UPDATE questions SET correct_answer = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (ANSWER_REPLACEMENTS[number], qid),
                )
                changed_fields.append("correct_answer")
            conn.execute(
                """
                INSERT INTO question_review_logs
                  (question_id, review_decision, review_notes, reviewer)
                VALUES (?, 'needs_review', ?, 'local_llm_ocr_review')
                """,
                (
                    qid,
                    "watermark_clean_ocr_cross_check; high_confidence_correction; changed="
                    + ",".join(changed_fields)
                    + "; "
                    "keep_needs_review_until_human_approval",
                ),
            )
            applied.append(number)
        if dry_run:
            conn.rollback()
        else:
            conn.commit()

    checked = json.loads(clean_json.read_text(encoding="utf-8"))
    for item in checked["questions"]:
        number = int(item["source_question_number"])
        if number in OPTION_REPLACEMENTS:
            item["review_notes"] = "local_llm_ocr_review: replaced options from watermark-clean OCR; keep pending human review"
        if number in OPTION_TEXT_REPLACEMENTS:
            option_map = OPTION_TEXT_REPLACEMENTS[number]
            for option in item.get("options") or []:
                if option.get("key") in option_map:
                    option["text"] = option_map[option["key"]]
            existing_keys = {option.get("key") for option in item.get("options") or []}
            for key, text in option_map.items():
                if key not in existing_keys:
                    item.setdefault("options", []).append({"key": key, "text": text})
        if number in STEM_REPLACEMENTS:
            item["stem"] = STEM_REPLACEMENTS[number]
        if number in ANSWER_REPLACEMENTS:
            item["correct_answer"] = ANSWER_REPLACEMENTS[number]
            item["review_notes"] = "local_llm_ocr_review: answer cross-checked from clean OCR and question knowledge; keep pending human review"
        item["review_status"] = "needs_review"
    checked_json.parent.mkdir(parents=True, exist_ok=True)
    checked_json.write_text(json.dumps(checked, ensure_ascii=False, indent=2), encoding="utf-8")

    audit_csv.parent.mkdir(parents=True, exist_ok=True)
    with audit_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "source_year",
                "source_question_number",
                "question_type",
                "decision",
                "changed_fields",
                "reason",
                "review_status",
            ],
        )
        writer.writeheader()
        for item in checked["questions"]:
            number = int(item["source_question_number"])
            fields: list[str] = []
            if number in OPTION_REPLACEMENTS:
                fields.append("options")
            if number in OPTION_TEXT_REPLACEMENTS:
                fields.append("option_text")
            if number in STEM_REPLACEMENTS:
                fields.append("stem")
            if number in ANSWER_REPLACEMENTS:
                fields.append("correct_answer")
            decision = "local_llm_corrected" if fields else "keep_existing"
            reason = (
                "clean OCR removes page watermark and restores a complete 4-option structure"
                if number in OPTION_REPLACEMENTS
                else (
                    "answer is legible in clean OCR and independently consistent with the question"
                    if number in ANSWER_REPLACEMENTS
                    else "clean OCR is not uniformly better; retain existing text for human review"
                )
            )
            writer.writerow(
                {
                    "source_year": 2024,
                    "source_question_number": number,
                    "question_type": item["question_type"],
                    "decision": decision,
                    "changed_fields": ",".join(fields),
                    "reason": reason,
                    "review_status": "needs_review",
                }
            )

    return {
        "db": str(db_path),
        "dry_run": dry_run,
        "backup": str(backup_path),
        "applied_questions": applied,
        "checked_json": str(checked_json),
        "audit_csv": str(audit_csv),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply conservative local-LLM review decisions for TEM4 2024 clean OCR.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--clean-json", type=Path, default=CLEAN_JSON)
    parser.add_argument("--checked-json", type=Path, default=CHECKED_JSON)
    parser.add_argument("--audit-csv", type=Path, default=AUDIT_CSV)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(apply(args.db, args.clean_json, args.checked_json, args.audit_csv, args.dry_run), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
