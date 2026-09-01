from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from seed_tem4_knowledge_points import seed as seed_tem4
from seed_tem8_knowledge_points import seed as seed_tem8


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
REPORT_DIR = ROOT / "data" / "processed" / "knowledge_tags"
BACKUP_DIR = ROOT / "data" / "processed" / "backups"

TYPE_PARENT = {
    "grammar_choice": "grammar",
    "literature_choice": "literature",
    "culture_choice": "culture",
    "reading_choice": "reading",
}

PREPOSITIONS = {
    "без", "в", "во", "для", "до", "за", "из", "из-за", "из-под", "к", "ко", "между",
    "на", "над", "о", "об", "обо", "около", "от", "перед", "по", "под", "при", "про",
    "с", "со", "у", "через", "благодаря", "вопреки", "согласно",
}
PRONOUNS = {
    "я", "ты", "он", "она", "оно", "мы", "вы", "они", "себя", "свой", "кто", "что",
    "какой", "который", "чей", "сколько", "никто", "ничто", "некого", "нечего", "некто",
    "нечто", "кто-то", "что-то", "кто-нибудь", "что-нибудь", "кто-либо", "что-либо",
    "кое-кто", "кое-что", "сам", "самый", "весь", "каждый", "другой", "иной", "любой",
}
CONJUNCTIONS = {
    "а", "и", "или", "либо", "но", "однако", "зато", "что", "чтобы", "как", "когда",
    "пока", "пока не", "если", "хотя", "поскольку", "потому что", "так как", "так что",
    "который", "какой", "где", "куда", "откуда", "зачем", "почему", "словно", "будто",
    "несмотря на то что", "в то время как", "с тех пор как", "до тех пор как",
}
MOTION_ROOTS = (
    "ид", "ход", "ех", "езд", "лет", "нос", "нес", "вез", "воз", "вед", "вод",
    "беж", "бег", "плы", "плав", "лез", "лаз", "полз", "гон", "кат",
)
NUMBER_WORDS = {
    "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять", "десять",
    "оба", "обе", "двое", "трое", "четверо", "первый", "второй", "третий", "половина",
    "четверть", "миллион", "миллиард", "сколько",
}
IMPERSONAL_PREDICATIVES = {
    "можно", "нельзя", "надо", "нужно", "необходимо", "следует", "жаль", "стыдно", "холодно",
    "тепло", "трудно", "легко", "некогда", "нездоровится", "хочется", "кажется",
}
PRONOUN_PREFIXES = (
    "кто", "кого", "кому", "кем", "ком", "что", "чего", "чему", "чем", "котор", "како",
    "чей", "чья", "чьё", "чьи", "сам", "себ", "ник", "не с кем", "ни с кем",
)


@dataclass(frozen=True)
class Decision:
    code: str
    confidence: float
    reason: str

    @property
    def needs_review(self) -> bool:
        return self.confidence < 0.72 or "." not in self.code


# Conservative local-model review for rows that cannot be decided reliably by
# surface-form rules alone. Keys use source identity so database rebuilds do not
# invalidate the decisions.
MANUAL_OVERRIDES: dict[tuple[str, int, str], Decision] = {
    ("TEM4_RU", 2017, "27"): Decision("grammar.pronoun", 0.94, "本地模型复核：人称代词格形式"),
    ("TEM4_RU", 2017, "30"): Decision("grammar.syntax_complex", 0.96, "本地模型复核：并列关联词"),
    ("TEM4_RU", 2017, "35"): Decision("grammar.aspect", 0.92, "本地模型复核：否定命令式中的动词体"),
    ("TEM4_RU", 2018, "17"): Decision("grammar.pronoun", 0.91, "本地模型复核：否定代词副词"),
    ("TEM4_RU", 2018, "28"): Decision("grammar.numeral", 0.96, "本地模型复核：集合数词变格"),
    ("TEM4_RU", 2018, "37"): Decision("grammar.preposition", 0.91, "本地模型复核：比较结构中的方向支配"),
    ("TEM4_RU", 2018, "39"): Decision("grammar.pronoun", 0.96, "本地模型复核：数量结构中的人称代词"),
    ("TEM4_RU", 2018, "55"): Decision("grammar.lexical_choice", 0.93, "本地模型复核：带前缀动词固定搭配"),
    ("TEM4_RU", 2019, "51"): Decision("grammar.preposition", 0.95, "本地模型复核：верить в себя 固定支配"),
    ("TEM4_RU", 2021, "42"): Decision("grammar.verb_form", 0.94, "本地模型复核：命令式人称与体"),
    ("TEM4_RU", 2021, "43"): Decision("grammar.syntax_complex", 0.97, "本地模型复核：选择关联词"),
    ("TEM4_RU", 2021, "46"): Decision("grammar.syntax_complex", 0.94, "本地模型复核：时间从句连接结构"),
    ("TEM4_RU", 2022, "17"): Decision("grammar.syntax_simple", 0.96, "本地模型复核：мне жаль 无人称结构"),
    ("TEM4_RU", 2022, "34"): Decision("grammar.aspect", 0.92, "本地模型复核：否定祈使与动词体"),
    ("TEM4_RU", 2023, "18"): Decision("grammar.syntax_complex", 0.96, "本地模型复核：настолько..., что... 结果结构"),
    ("TEM4_RU", 2023, "29"): Decision("grammar.verb_form", 0.94, "本地模型复核：虚拟条件结构"),
    ("TEM4_RU", 2023, "35"): Decision("grammar.aspect", 0.93, "本地模型复核：命令式动词体与语境"),
    ("TEM4_RU", 2023, "38"): Decision("grammar.adjective_adverb", 0.96, "本地模型复核：比较级形式"),
    ("TEM4_RU", 2023, "44"): Decision("grammar.syntax_simple", 0.94, "本地模型复核：кому осталось 无人称结构"),
    ("TEM4_RU", 2023, "51"): Decision("grammar.case", 0.95, "本地模型复核：поручить кому 格支配"),
    ("TEM4_RU", 2023, "53"): Decision("grammar.lexical_choice", 0.95, "本地模型复核：名词词义与搭配"),
    ("TEM4_RU", 2024, "30"): Decision("grammar.syntax_complex", 0.95, "本地模型复核：时间从句连接词"),
    ("TEM4_RU", 2024, "38"): Decision("grammar.case", 0.86, "本地模型复核：时间持续结构的格形式"),
    ("TEM4_RU", 2024, "52"): Decision("grammar.preposition", 0.95, "本地模型复核：требовать от кого 支配"),
    ("TEM4_RU", 2024, "57"): Decision("grammar.pronoun", 0.95, "本地模型复核：хватать кому 人称代词格"),
    ("TEM8_RU", 2017, "21"): Decision("grammar.syntax_complex", 0.94, "本地模型复核：程度结果关联结构"),
    ("TEM8_RU", 2017, "23"): Decision("grammar.pronoun", 0.92, "本地模型复核：指示代词格形式"),
    ("TEM8_RU", 2017, "24"): Decision("grammar.syntax_complex", 0.96, "本地模型复核：并列关联词"),
    ("TEM8_RU", 2017, "28"): Decision("grammar.lexical_choice", 0.91, "本地模型复核：同根词词义辨析"),
    ("TEM8_RU", 2018, "22"): Decision("grammar.syntax_complex", 0.95, "本地模型复核：程度从句关联结构"),
    ("TEM8_RU", 2018, "26"): Decision("grammar.lexical_choice", 0.94, "本地模型复核：动词与名词固定搭配"),
    ("TEM8_RU", 2018, "29"): Decision("grammar.lexical_choice", 0.94, "本地模型复核：近义前缀动词辨析"),
    ("TEM8_RU", 2019, "18"): Decision("grammar.syntax_complex", 0.94, "本地模型复核：让步衔接表达"),
    ("TEM8_RU", 2019, "28"): Decision("grammar.lexical_choice", 0.96, "本地模型复核：научный подход 固定搭配"),
    ("TEM8_RU", 2019, "32"): Decision("grammar.lexical_choice", 0.95, "本地模型复核：固定熟语辨析"),
    ("TEM8_RU", 2021, "24"): Decision("grammar.syntax_complex", 0.94, "本地模型复核：关联程度结构"),
    ("TEM8_RU", 2023, "29"): Decision("grammar.pronoun", 0.95, "本地模型复核：人称代词格与指代"),
    ("TEM8_RU", 2023, "32"): Decision("grammar.style", 0.98, "本地模型复核：修辞手法辨析"),
    ("TEM8_RU", 2024, "20"): Decision("grammar.syntax_complex", 0.95, "本地模型复核：交替关联词"),
    ("TEM8_RU", 2024, "22"): Decision("grammar.syntax_complex", 0.92, "本地模型复核：как бы не 警惕结构"),
    ("TEM8_RU", 2024, "32"): Decision("grammar.lexical_choice", 0.93, "本地模型复核：熟语和固定表达"),
}


def words(value: str) -> list[str]:
    return re.findall(r"[а-яё-]+", (value or "").lower())


def option_heads(options: list[str]) -> list[str]:
    return [tokens[0] for value in options if (tokens := words(value))]


def starts_with_preposition(value: str) -> bool:
    tokens = words(value)
    return bool(tokens and tokens[0] in PREPOSITIONS)


def is_infinitive(word: str) -> bool:
    return bool(re.search(r"(?:ть|ти|чь)(?:ся)?$", word))


def is_finite_verb(word: str) -> bool:
    return bool(
        re.search(
            r"(?:ю|у|ешь|ёшь|ишь|ет|ёт|ит|ем|ём|им|ете|ёте|ите|ют|ут|ят|ат|л|ла|ло|ли|й|йте|ите)(?:ся)?$",
            word,
        )
    )


def common_prefix_length(values: list[str]) -> int:
    if not values:
        return 0
    prefix = values[0]
    for value in values[1:]:
        while prefix and not value.startswith(prefix):
            prefix = prefix[:-1]
    return len(prefix)


def classify_grammar(stem: str, options: list[str]) -> Decision:
    text = " ".join([stem, *options]).lower()
    heads = option_heads(options)
    tokens = words(text)

    if any(any(root in word for root in MOTION_ROOTS) for word in heads) and sum(
        is_infinitive(word) or is_finite_verb(word) for word in heads
    ) >= 2:
        return Decision("grammar.motion_verbs", 0.91, "选项集中考查运动动词")

    gerund_hits = sum(
        (len(word) >= 6 and bool(re.search(r"(?:ая|яя)(?:сь)?$", word)))
        or (len(word) >= 5 and bool(re.search(r"(?:в|вши|ши)(?:сь)?$", word)))
        for word in heads
    )
    if gerund_hits >= 2:
        return Decision("grammar.adverbial_participle", 0.84, "选项包含副动词与谓语形式辨析")

    participle_hits = sum(
        bool(
            re.search(r"(?:ющ|ущ|ащ|ящ|вш|енн|анн|янн)[а-яё]*(?:ся)?$", word)
            or re.search(r"(?:ем|им)(?:ый|ая|ое|ые|ого|ой|ому|ым|ом|ую|ыми|ых)$", word)
        )
        for word in heads
    )
    if participle_hits >= 2:
        return Decision("grammar.participle", 0.86, "选项集中考查形动词形式")

    normalized_options = [" ".join(words(value)) for value in options]
    conjunction_hits = sum(value in CONJUNCTIONS for value in normalized_options)
    if conjunction_hits >= 2 or (
        stem.count(",") >= 1 and sum(value in CONJUNCTIONS for value in normalized_options) >= 1
    ):
        return Decision("grammar.syntax_complex", 0.84, "连接词或从句关系辨析")

    pronoun_hits = sum(
        word in PRONOUNS or any(value.startswith(prefix) for prefix in PRONOUN_PREFIXES)
        for word, value in zip(heads, normalized_options)
    )
    if pronoun_hits >= 2:
        return Decision("grammar.pronoun", 0.86, "选项集中考查代词或指代")

    if sum(word in NUMBER_WORDS for word in tokens) >= 2:
        return Decision("grammar.numeral", 0.82, "题干或选项包含数词与数量结构")

    preposition_hits = sum(starts_with_preposition(value) for value in options)
    tails = [tokens[-1] for value in options if (tokens := words(value))]
    tail_prefix = common_prefix_length(tails)
    if preposition_hits >= 1 and len(tails) >= 3 and tail_prefix >= 3:
        return Decision("grammar.preposition", 0.86, "前置词与同一中心词的格支配辨析")
    if preposition_hits >= max(2, len(options) - 1):
        return Decision("grammar.preposition", 0.88, "选项主要区别在前置词及其支配")

    if heads and all(is_infinitive(word) for word in heads):
        prefix = common_prefix_length([word.removesuffix("ся") for word in heads])
        if prefix >= 3:
            return Decision("grammar.aspect", 0.78, "同根不定式体现动词体或动作方式差异")
        return Decision("grammar.lexical_choice", 0.82, "不同动词的词义与搭配辨析")

    verb_hits = sum(is_infinitive(word) or is_finite_verb(word) for word in heads)
    if verb_hits >= max(2, len(heads) - 1):
        prefix = common_prefix_length([word.removesuffix("ся") for word in heads])
        if prefix >= 4:
            return Decision("grammar.verb_form", 0.83, "同一动词的时态、语气或形式辨析")
        return Decision("grammar.lexical_choice", 0.76, "动词词义或固定搭配辨析")

    if len(heads) >= 3 and (common_prefix_length(heads) >= 3 or tail_prefix >= 3):
        return Decision("grammar.case", 0.81, "同根名词、形容词或代词的格形式辨析")

    if sum(word in IMPERSONAL_PREDICATIVES for word in tokens) >= 2:
        return Decision("grammar.syntax_simple", 0.78, "无人称结构或状态谓语辨析")

    if any(marker in text for marker in ("стиль", "разговорн", "книжн", "официальн", "устаревш", "переносн")):
        return Decision("grammar.style", 0.82, "语体、修辞或词语色彩辨析")

    return Decision("grammar.lexical_choice", 0.68, "默认归入词义辨析与固定搭配，建议复核")


def classify_reading(stem: str) -> Decision:
    text = stem.lower()
    if any(marker in text for marker in ("основная мысль", "главная мысль", "главный смысл", "тема текста", "озаглав", "речь идёт", "речь идет", "идёт речь", "идет речь")):
        return Decision("reading.main_idea", 0.90, "题干要求概括主旨、主题或标题")
    if any(marker in text for marker in ("значение слова", "означает слово", "слово означает", "заменить слов", "выражение означает", "понимать выражение")):
        return Decision("reading.vocabulary_context", 0.91, "题干要求判断语境词义")
    if any(marker in text for marker in ("отношение автора", "позиция автора", "мнение автора", "автор считает", "тон текста")):
        return Decision("reading.attitude", 0.88, "题干要求判断作者观点或态度")
    if any(marker in text for marker in ("структур", "абзац", "последовательност", "связь между", "разделить текст")):
        return Decision("reading.structure", 0.86, "题干要求判断篇章结构或段落关系")
    if any(marker in text for marker in ("можно сделать вывод", "следует из текста", "можно предположить", "скорее всего", "подразумевает")):
        return Decision("reading.inference", 0.88, "题干要求根据原文推断")
    return Decision("reading.detail", 0.79, "默认按原文事实定位题处理")


def classify_culture(stem: str, options: list[str]) -> Decision:
    text = " ".join([stem, *options]).lower()
    groups = [
        ("culture.politics", ("конституц", "президент", "дума", "парламент", "правительств", "федерац", "министр", "совет федерации")),
        ("culture.symbols", ("флаг", "герб", "гимн", "праздник", "день россии", "новый год", "победы")),
        ("culture.geography", ("река", "озеро", "море", "гора", "город", "область", "край", "республика", "сибир", "урал", "ресурс", "столиц")),
        ("culture.education_science", ("университет", "академ", "музей", "театр", "наук", "образован", "библиотек", "консерватор")),
        ("culture.history", ("век", "год", "царь", "император", "революц", "войн", "ссср", "русь", "пётр", "ленин")),
    ]
    for code, markers in groups:
        if any(marker in text for marker in markers):
            return Decision(code, 0.82, "国情题关键词匹配到细分主题")
    return Decision("culture.society", 0.73, "社会生活、民族文化或传统常识")


def classify_literature(stem: str, options: list[str]) -> Decision:
    text = " ".join([stem, *options]).lower()
    if any(marker in text for marker in ("стилистическ", "прием", "приём", "метафор", "метоним", "синекдох", "олицетвор", "антитез", "оксюморон", "гипербол", "перифраз")):
        return Decision("literature.genre_terms", 0.91, "修辞手法或文学术语")
    if any(marker in text for marker in ("направлен", "реализм", "романтизм", "символизм", "акмеизм", "футуризм", "модернизм", "школ", "деревенской проз", "представител")):
        return Decision("literature.history_movements", 0.89, "文学史、流派或代表群体")
    if any(marker in text for marker in ("главн", "геро", "образ", "персонаж", "судьб", "смысл произвед", "рассказывает о", "изображается")):
        return Decision("literature.work_content", 0.88, "作品人物、情节或主题内容")
    return Decision("literature.author_work", 0.86, "作家、作品、名句出处或创作信息")


def classify(question_type: str, stem: str, options: list[str]) -> Decision:
    if question_type == "grammar_choice":
        return classify_grammar(stem, options)
    if question_type == "reading_choice":
        return classify_reading(stem)
    if question_type == "culture_choice":
        return classify_culture(stem, options)
    if question_type == "literature_choice":
        return classify_literature(stem, options)
    raise ValueError(f"Unsupported formal question type: {question_type}")


def load_questions(conn: sqlite3.Connection, exam_codes: list[str]) -> list[sqlite3.Row]:
    placeholders = ", ".join("?" for _ in exam_codes)
    return conn.execute(
        f"""
        SELECT
          q.id, es.code AS exam_system, q.source_year, q.source_question_number,
          q.stem, qt.code AS question_type,
          GROUP_CONCAT(qo.option_text, ' || ') AS option_texts
        FROM questions q
        JOIN exam_systems es ON es.id = q.exam_system_id
        JOIN question_types qt ON qt.id = q.question_type_id
        LEFT JOIN question_options qo ON qo.question_id = q.id
        WHERE q.review_status = 'approved'
          AND q.source_usage = 'practice'
          AND es.code IN ({placeholders})
          AND qt.code IN ('grammar_choice', 'literature_choice', 'culture_choice', 'reading_choice')
        GROUP BY q.id
        ORDER BY es.code, q.source_year, CAST(q.source_question_number AS INTEGER), q.id
        """,
        exam_codes,
    ).fetchall()


def point_ids(conn: sqlite3.Connection, exam_system: str) -> dict[str, int]:
    return {
        str(code): int(point_id)
        for code, point_id in conn.execute(
            """
            SELECT kp.code, kp.id
            FROM knowledge_points kp
            JOIN exam_systems es ON es.id = kp.exam_system_id
            WHERE es.code = ?
            """,
            (exam_system,),
        )
    }


def backup_database(db_path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / f"russian_ai_tutor_before_fine_knowledge_tags_{stamp}.sqlite"
    shutil.copy2(db_path, target)
    return target


def run(db_path: Path, exam_codes: list[str], apply: bool, report_path: Path) -> dict[str, Any]:
    backup_path = backup_database(db_path) if apply else None
    if apply:
        seed_tem8(reset=False, db_path=db_path)
        seed_tem4(db_path)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        questions = load_questions(conn, exam_codes)
        ids_by_exam = {code: point_ids(conn, code) for code in exam_codes}
        rows: list[dict[str, Any]] = []
        summary: dict[str, int] = {}
        review_count = 0

        for row in questions:
            options = str(row["option_texts"] or "").split(" || ")
            identity = (str(row["exam_system"]), int(row["source_year"]), str(row["source_question_number"]))
            manual_decision = MANUAL_OVERRIDES.get(identity)
            decision = manual_decision or classify(str(row["question_type"]), str(row["stem"]), options)
            final_code = TYPE_PARENT[str(row["question_type"])] if decision.needs_review else decision.code
            status = "needs_review" if decision.needs_review else "manual_approved" if manual_decision else "auto_approved"
            if apply and final_code not in ids_by_exam[str(row["exam_system"])]:
                raise ValueError(f"Missing {row['exam_system']} knowledge point: {final_code}")

            summary[final_code] = summary.get(final_code, 0) + 1
            review_count += int(decision.needs_review)
            rows.append(
                {
                    "question_id": int(row["id"]),
                    "exam_system": row["exam_system"],
                    "source_year": row["source_year"],
                    "source_question_number": row["source_question_number"],
                    "question_type": row["question_type"],
                    "suggested_code": decision.code,
                    "applied_code": final_code,
                    "confidence": f"{decision.confidence:.2f}",
                    "tag_status": status,
                    "reason": decision.reason,
                    "stem": row["stem"],
                }
            )

            if apply:
                conn.execute("DELETE FROM question_knowledge_points WHERE question_id = ?", (int(row["id"]),))
                conn.execute(
                    """
                    INSERT INTO question_knowledge_points (question_id, knowledge_point_id, weight)
                    VALUES (?, ?, ?)
                    """,
                    (
                        int(row["id"]),
                        ids_by_exam[str(row["exam_system"])][final_code],
                        decision.confidence,
                    ),
                )

        if apply:
            conn.commit()
        else:
            conn.rollback()

    with report_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)

    return {
        "dry_run": not apply,
        "exam_systems": exam_codes,
        "formal_questions": len(rows),
        "fine_tagged": len(rows) - review_count,
        "needs_review_parent_only": review_count,
        "report": str(report_path),
        "backup": str(backup_path) if backup_path else None,
        "by_applied_code": dict(sorted(summary.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Conservatively assign fine knowledge tags to formal TEM4/TEM8 questions.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--exam", action="append", choices=["TEM4_RU", "TEM8_RU"], default=[])
    parser.add_argument("--apply", action="store_true", help="Write tags to the database. Default is dry-run.")
    parser.add_argument("--report", type=Path, default=REPORT_DIR / "question_knowledge_tagging_review.csv")
    args = parser.parse_args()
    exam_codes = args.exam or ["TEM4_RU", "TEM8_RU"]
    print(json.dumps(run(args.db, exam_codes, args.apply, args.report), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
