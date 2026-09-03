from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"

# code, parent, name_zh, name_ru, category, description, sort_order
POINTS: list[tuple[str, str | None, str, str, str, str, int]] = [
    ("grammar", None, "语法与词汇", "Грамматика и лексика", "grammar", "专八综合知识中的语法、词汇和语体相关考点。", 100),
    ("grammar.forms", "grammar", "词形与动词系统", "Формы слов и система глагола", "grammar", "格、代词、数词、形容词与副词变化，以及动词体、运动动词、时态语气、形动词和副动词。", 101),
    ("grammar.collocation", "grammar", "词义、前置词与搭配", "Лексика, предлоги и сочетаемость", "grammar", "近义词辨析、前置词支配、固定搭配、惯用表达和语义色彩。", 102),
    ("grammar.sentence", "grammar", "句法、连接与表达", "Синтаксис, связь и выражение", "grammar", "简单句、复合句、连接词、语体修辞和语境表达。", 103),
    ("grammar.case", "grammar", "名词格与支配关系", "Падежи и управление", "grammar", "名词、代词、形容词格形式，以及动词、形容词、名词对格的支配。", 110),
    ("grammar.preposition", "grammar", "前置词搭配", "Предлоги", "grammar", "前置词与格、固定搭配、意义辨析。", 120),
    ("grammar.aspect", "grammar", "动词体", "Вид глагола", "grammar", "完成体与未完成体的意义、时态和语境选择。", 130),
    ("grammar.motion_verbs", "grammar", "运动动词", "Глаголы движения", "grammar", "定向/不定向运动动词、带前缀运动动词和语义差异。", 140),
    ("grammar.verb_form", "grammar", "动词时态、语气与命令式", "Время, наклонение и императив", "grammar", "时态、条件式、命令式、无人称结构中的动词形式。", 150),
    ("grammar.participle", "grammar", "形动词", "Причастие", "grammar", "主动/被动形动词、短尾形式、形动词短语。", 160),
    ("grammar.adverbial_participle", "grammar", "副动词", "Деепричастие", "grammar", "副动词形式、逻辑主语一致、时间和方式意义。", 170),
    ("grammar.numeral", "grammar", "数词与数量结构", "Числительные", "grammar", "数词变格、集合数词、数量短语和谓语配合。", 180),
    ("grammar.pronoun", "grammar", "代词与指代", "Местоимения", "grammar", "人称、反身、指示、不定、否定代词及其指代关系。", 190),
    ("grammar.adjective_adverb", "grammar", "形容词、副词与比较级", "Прилагательные, наречия и степени сравнения", "grammar", "形容词长短尾、副词形式、比较级和最高级，以及相关谓语结构。", 195),
    ("grammar.syntax_simple", "grammar", "简单句句法", "Синтаксис простого предложения", "grammar", "主谓一致、无主句、不定人称句、句子成分和词序。", 200),
    ("grammar.syntax_complex", "grammar", "复合句与连接词", "Сложное предложение и союзы", "grammar", "从句类型、连接词选择、并列和主从复合句逻辑。", 210),
    ("grammar.lexical_choice", "grammar", "词义辨析与固定搭配", "Лексическая сочетаемость", "grammar", "近义词、固定搭配、惯用表达和语义色彩。", 220),
    ("grammar.style", "grammar", "语体与修辞", "Стиль и риторика", "grammar", "书面语、口语、正式语体、修辞表达和语境适配。", 230),
    ("literature", None, "俄罗斯文学", "Русская литература", "literature", "专八文学常识、作家作品、文学史和文学术语。", 300),
    ("literature.knowledge", "literature", "作家、作品与文学常识", "Авторы, произведения и история литературы", "literature", "作家作品、人物情节、名句出处、文学史、流派和文学术语。", 301),
    ("literature.author_work", "literature", "作家与作品", "Авторы и произведения", "literature", "作家、代表作、创作年代、名句出处和作品归属。", 310),
    ("literature.work_content", "literature", "人物、名句与情节", "Герои, цитаты и сюжет", "literature", "作品人物、人物关系、名句、核心情节和主题内容。", 320),
    ("literature.history_movements", "literature", "文学史与流派", "История и направления литературы", "literature", "文学史时期、文学流派、文学团体及代表作家。", 330),
    ("literature.genre_terms", "literature", "体裁与文学术语", "Жанры и литературные термины", "literature", "小说、诗歌、戏剧、修辞手法、叙事和其他文学术语。", 340),
    ("culture", None, "俄罗斯国情", "Страноведение России", "culture", "专八国情常识、历史地理、政治文化和社会生活。", 400),
    ("culture.knowledge", "culture", "俄罗斯国情常识", "Страноведение России", "culture", "俄罗斯历史、地理、政治制度、国家象征、文化机构和社会传统。", 401),
    ("culture.geography", "culture", "地理与行政区划", "География и административное деление", "culture", "地理位置、河流湖泊、城市、联邦主体和自然资源。", 410),
    ("culture.history", "culture", "历史事件与时代", "История России", "culture", "基辅罗斯、沙俄、苏联、现代俄罗斯的重要历史节点。", 420),
    ("culture.politics", "culture", "政治制度与国家机构", "Политическая система", "culture", "宪法、总统、议会、政府、联邦制度和国家机构。", 430),
    ("culture.symbols", "culture", "国家象征与节日", "Государственные символы и праздники", "culture", "国旗、国徽、国歌、重要节日和纪念日。", 440),
    ("culture.education_science", "culture", "教育、科技与文化机构", "Образование, наука и культура", "culture", "教育制度、科学院、大学、博物馆、剧院和文化机构。", 450),
    ("culture.society", "culture", "社会生活与传统", "Общество и традиции", "culture", "民族、宗教、生活习俗、饮食、艺术和社会文化常识。", 460),
    ("reading", None, "阅读理解", "Чтение", "reading", "专八阅读理解题的能力点和错因类型。", 500),
    ("reading.comprehension", "reading", "阅读理解", "Понимание текста", "reading", "理解文章主旨、事实、语境、推断和篇章关系。", 501),
    ("reading.main_idea", "reading", "主旨大意", "Основная мысль", "reading", "识别文章中心、段落主旨和标题概括。", 510),
    ("reading.detail", "reading", "事实细节", "Детали текста", "reading", "定位原文信息、数字、原因、人物行为和事实对应。", 520),
    ("reading.inference", "reading", "推理判断", "Выводы и импликации", "reading", "根据上下文推断隐含意义、原因结果和作者未明说的信息。", 530),
    ("reading.vocabulary_context", "reading", "语境词义", "Значение слова в контексте", "reading", "根据上下文判断词义、代词指代、同义替换和表达色彩。", 540),
    ("reading.structure", "reading", "篇章结构", "Структура текста", "reading", "段落关系、承接转折、论证结构和信息组织。", 550),
    ("reading.attitude", "reading", "作者态度与语气", "Позиция автора", "reading", "判断作者观点、评价倾向、情感色彩和语气。", 560),
]


def get_tem8_exam_system_id(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT id FROM exam_systems WHERE code = 'TEM8_RU'").fetchone()
    if row is None:
        raise ValueError("Missing exam system TEM8_RU. Initialize the database first.")
    return int(row[0])


def upsert_point(
    conn: sqlite3.Connection,
    exam_system_id: int,
    item: tuple[str, str | None, str, str, str, str, int],
    id_by_code: dict[str, int],
) -> int:
    code, parent_code, name_zh, name_ru, category, description, sort_order = item
    parent_id = None
    if parent_code:
        parent_id = id_by_code.get(parent_code)
        if parent_id is None:
            raise ValueError(f"Parent knowledge point not found: {parent_code}")

    existing = conn.execute(
        "SELECT id FROM knowledge_points WHERE exam_system_id = ? AND code = ?",
        (exam_system_id, code),
    ).fetchone()
    if existing:
        point_id = int(existing[0])
        conn.execute(
            """
            UPDATE knowledge_points
            SET parent_id = ?, name_zh = ?, name_ru = ?, category = ?,
                description = ?, sort_order = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (parent_id, name_zh, name_ru, category, description, sort_order, point_id),
        )
        return point_id

    cursor = conn.execute(
        """
        INSERT INTO knowledge_points (
          exam_system_id, parent_id, code, name_zh, name_ru,
          category, description, sort_order
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (exam_system_id, parent_id, code, name_zh, name_ru, category, description, sort_order),
    )
    return int(cursor.lastrowid)


def seed(reset: bool, db_path: Path = DB_PATH) -> dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        exam_system_id = get_tem8_exam_system_id(conn)

        if reset:
            linked_count = conn.execute(
                "SELECT COUNT(*) FROM question_knowledge_points"
            ).fetchone()[0]
            if linked_count:
                raise ValueError(
                    "Cannot reset knowledge points while question_knowledge_points has links."
                )
            conn.execute("DELETE FROM knowledge_points WHERE exam_system_id = ?", (exam_system_id,))

        id_by_code = {
            code: int(point_id)
            for code, point_id in conn.execute(
                "SELECT code, id FROM knowledge_points WHERE exam_system_id = ?",
                (exam_system_id,),
            ).fetchall()
        }

        for item in POINTS:
            code = item[0]
            id_by_code[code] = upsert_point(conn, exam_system_id, item, id_by_code)

        conn.commit()
        counts = [
            {"category": category, "count": int(count)}
            for category, count in conn.execute(
                """
                SELECT category, COUNT(*)
                FROM knowledge_points
                WHERE exam_system_id = ?
                GROUP BY category
                ORDER BY category
                """,
                (exam_system_id,),
            ).fetchall()
        ]

    return {"seeded": len(POINTS), "counts": counts}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed TEM8 knowledge points.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing TEM8 knowledge points first. Refuses to run if question links exist.",
    )
    args = parser.parse_args()
    print(json.dumps(seed(reset=args.reset), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
