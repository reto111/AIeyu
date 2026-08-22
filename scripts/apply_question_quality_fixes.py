from __future__ import annotations

import argparse
import csv
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
BACKUP_DIR = ROOT / "data" / "processed" / "backups"
OUT_DIR = ROOT / "data" / "processed" / "question_quality"
REVIEWER = "local_quality_audit"


QUESTION_FIXES = {
    (2017, "31"): {
        "stem": "Встреча президентов двух стран ____ прочную основу экономического сотрудничества.",
        "options": {"D": "приложила"},
        "note": "补回填空位置，清理 D 选项页脚噪声。",
    },
    (2017, "38"): {
        "stem": "Произведение И.А. Бунина ____ называют «энциклопедией любви».",
        "note": "根据原文和正确答案修复被作者缩写干扰的题干。",
    },
    (2017, "18"): {
        "stem": "____ приступить к составлению контракта, необходимо собрать максимум информации о партнере.",
        "options": {"A": "Как только"},
        "note": "补回句首填空位置，清理 A 选项 OCR 符号。",
    },
    (2017, "20"): {
        "stem": "Никакая иная сила не делает человека великим и мудрым, ____ делает сила коллективного труда.",
        "options": {"A": "так"},
        "note": "修复题干 OCR 噪声和断行，统一 A 选项大小写。",
    },
    (2017, "23"): {
        "stem": "____, как Менделеев или Ломоносов, не в каждой стране рождаются.",
        "options": {"B": "Таких"},
        "note": "补回句首填空位置，清理 B 选项 OCR 符号。",
    },
    (2017, "29"): {
        "stem": "Роль вузов заключается в том, чтобы помочь студентам найти место и полностью ____ свои способности.",
        "note": "修复 TOM -> том 的 OCR 错误，并补回填空位置。",
    },
    (2017, "33"): {
        "stem": "В предложении «Мы дружно встали стеной за детей своих» используется стилистический прием ____.",
        "options": {"D": "олицетворение"},
        "note": "补回填空位置，清理 D 选项栏目标题噪声。",
    },
    (2017, "36"): {
        "stem": "____ не принадлежит к числу поэтов XX века.",
        "note": "根据选项和正确答案补全被页脚干扰的文学题题干。",
    },
    (2017, "56"): {
        "options": {"B": "Бороться со взрослым миром.", "D": "Существовать бездумно и ничего не делать."},
        "note": "清理阅读选项中的 OCR 尾部噪声。",
    },
    (2017, "43"): {
        "stem": "А.П. Бородин — известный композитор, написавший музыку к опере ____.",
        "options": {"A": "«Пиковая дама»", "D": "«Иван Сусанин»"},
        "note": "修复 А.П. 被误切为 A 选项、清理 D 选项页脚噪声。",
    },
    (2018, "22"): {
        "stem": "При чтении этого романа остается только удивляться, ____ богата человеческая фантазия.",
        "note": "补回选择填空位置。",
    },
    (2018, "16"): {
        "stem": "Наташа ни за что это ____, она на это просто не способна.",
        "options": {"A": "говорит"},
        "note": "补回填空位置，清理 A 选项 OCR 符号。",
    },
    (2018, "25"): {
        "stem": "Петров не хотел ехать с охотниками в тайгу и было ____ отказываться, но те не отступали.",
        "options": {"D": "начал"},
        "note": "根据固定结构 было начал/начала... 补全题干，清理 D 选项 OCR 符号。",
    },
    (2018, "26"): {
        "stem": "В жизни должно быть много всяких дел, и увлечению мало места ____.",
        "note": "修复题干 OCR 噪声并补回谓语填空位置。",
    },
    (2018, "33"): {
        "stem": "В предложении «Ученик — это не сосуд, который надо наполнить, а факел, который надо зажечь» используется стилистический прием ____.",
        "options": {"A": "метафора", "D": "перифраза"},
        "note": "修复 зажечь 断裂和选项/栏目噪声。",
    },
    (2018, "38"): {
        "stem": "Центральным и самым сложным образом романа «Тихий Дон» является ____.",
        "note": "补全文学题题干。",
    },
    (2018, "39"): {
        "stem": "Произведение ____ А.И. Солженицына рассказывает о России 1914-1917 годов.",
        "options": {"A": "«Жизнь Арсеньева»", "C": "«Мастер и Маргарита»", "D": "«Красное колесо»"},
        "note": "根据作品与作者关系补全文学题题干，清理栏目标题噪声。",
    },
    (2018, "40"): {
        "stem": "Раскол русской православной церкви произошел в ____ веке.",
        "options": {"A": "XV"},
        "note": "修正罗马数字 OCR 错误：ХУ -> XV，并补回填空位置。",
    },
    (2018, "47"): {
        "options": {"D": "Его музыка удивляла и настораживала их."},
        "note": "清理阅读 D 选项 OCR 尾部噪声。",
    },
    (2018, "52"): {
        "options": {"C": "Образ Клааса из Голландии."},
        "note": "清理阅读 C 选项 OCR 符号。",
    },
    (2018, "60"): {
        "options": {"D": "Автор нашел эту книгу у себя, на второй полке четвертого шкафа."},
        "note": "清理阅读 D 选项页脚噪声。",
    },
    (2019, "55"): {
        "options": {"B": "Они считают, что сотовый телефон - «антиизобретение» №1."},
        "note": "将 OCR 产生的中文书名号改为俄文引号。",
    },
    (2021, "19"): {
        "stem": "Когда НДС ____ на уровне 10%, люди стали инвестировать в сферу услуг, открывая новые кафе и рестораны.",
        "note": "补回填空位置并合并 рестораны 断行。",
    },
    (2023, "29"): {
        "stem": "Цель формируется из мечты. Мечта растет, ____ нет конца и края, а у цели есть результат.",
        "note": "修正 ф->а 的 OCR 错误，并将正确答案位置显式留空。",
    },
    (2024, "23"): {
        "stem": "Интересному человеку ____ сделать интересной даже самую скучную работу.",
        "note": "补回选择填空位置。",
    },
    (2024, "19"): {
        "stem": "Мама настаивает на том, ____ во время ужина мы собирались за столом всей семьей.",
        "options": {"D": "как будто"},
        "note": "补回从属连词填空位置，清理 D 选项页脚噪声。",
    },
    (2024, "25"): {
        "stem": "Анна обладала решительным и целеустремленным характером, и в этом она определенно пошла ____.",
        "note": "合并断行连字符并补回选择填空位置。",
    },
    (2024, "26"): {
        "stem": "В некоторых странах для получения самой чистой и приятной ____ воды переливают ее из сосуда в сосуд по нескольку раз.",
        "options": {"B": "к вкусу"},
        "note": "合并断行连字符，补回填空位置，修正 B 选项 OCR：квкусу -> к вкусу。",
    },
    (2024, "28"): {
        "stem": "От волнения у Наташи в глазах ____, и она не могла ничего разглядеть.",
        "options": {"B": "потемнело"},
        "note": "补回填空位置，清理 B 选项页脚噪声。",
    },
    (2024, "33"): {
        "stem": "В строке А.С. Пушкина «Ты богат, я очень беден. Ты прозаик, я поэт» используется стилистический прием ____.",
        "options": {"A": "олицетворение", "D": "оксюморон"},
        "note": "修复 А.С. 被误切为 A 选项，清理栏目标题噪声。",
    },
    (2024, "37"): {
        "stem": "Стихотворение «Не жалею, не зову, не плачу...» принадлежит перу ____.",
        "note": "清理题干末尾 OCR 噪声并补回填空位置。",
    },
    (2024, "39"): {
        "stem": "В повести В.Г. Распутина «Живи и помни» смысл произведения раскрывается через судьбу двух людей — ____.",
        "options": {"B": "Настены и Андрея", "D": "Дарьи и Павла"},
        "note": "修复 В.Г. 被误切为 B 选项，清理栏目标题噪声。",
    },
    (2024, "36"): {
        "stem": "В поэме Н.А. Некрасова ____ рассказывается о путешествии семерых крестьянских мужиков по всей Руси с целью поиска счастливого человека.",
        "note": "清理题干中页脚/OCR 噪声并补回作品名填空位置。",
    },
    (2024, "42"): {
        "stem": "____ является организатором и идейным руководителем Товарищества передвижных художественных выставок.",
        "options": {"D": "И.Н. Крамской"},
        "note": "合并断行并清理 D 选项页脚噪声。",
    },
    (2024, "57"): {
        "options": {"A": "Он хотел выразить ей свою благодарность."},
        "note": "清理阅读 A 选项页脚噪声。",
    },
    (2024, "60"): {
        "options": {"B": "Николай Зверев отказался принять его в ученики."},
        "note": "清理阅读 B 选项页脚噪声。",
    },
    (2024, "75"): {
        "stem": "Почему градозащитники могли добиваться сохранения архитектурных памятников в XIX — начале XX века?",
        "options": {"D": "Потому что они могли обращаться за поддержкой в высшие инстанции."},
        "note": "修正 начале 的 OCR 错误并清理 D 选项页脚噪声。",
    },
}


UNRESOLVED_ITEMS = {
    (2017, "24"): "题干与多个选项 OCR 严重损坏，无法可靠复原原始搭配。",
    (2017, "27"): "题干主体和多个选项 OCR 严重损坏，无法可靠复原语境。",
    (2017, "39"): "题干与 A/C 选项残缺，无法可靠确认全部选项。",
    (2017, "47"): "阅读选项多处截断，影响作答判断。",
    (2017, "58"): "阅读题干和多个选项 OCR 残缺，影响理解。",
    (2017, "59"): "阅读题干和 A 选项 OCR 残缺，无法可靠确认干扰项。",
    (2017, "64"): "阅读题干和多个选项截断，影响作答判断。",
    (2017, "65"): "阅读题干和多个选项 OCR 严重损坏，无法可靠复原。",
    (2018, "27"): "题干主体 OCR 严重损坏，只能确认选项与答案，无法可靠复原完整语境，临时移出练习池。",
    (2018, "28"): "题干和选项 OCR 严重损坏，且正确答案与常见搭配疑似不一致，需核对原卷。",
    (2018, "50"): "阅读题干和多个选项 OCR 严重损坏，无法可靠复原。",
    (2018, "64"): "阅读题干和多个选项 OCR 严重损坏，无法可靠复原。",
    (2018, "65"): "阅读题干和部分选项 OCR 残缺，需核对原卷。",
}


def find_question(con: sqlite3.Connection, year: int, number: str) -> sqlite3.Row:
    row = con.execute(
        """
        select id, stem, review_status, source_usage
        from questions
        where source_year = ? and source_question_number = ?
        """,
        (year, number),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"Question not found: {year} #{number}")
    return row


def add_log(con: sqlite3.Connection, question_id: int, decision: str, note: str) -> None:
    exists = con.execute(
        """
        select 1
        from question_review_logs
        where question_id = ? and review_decision = ? and review_notes = ? and reviewer = ?
        limit 1
        """,
        (question_id, decision, note, REVIEWER),
    ).fetchone()
    if exists:
        return
    con.execute(
        """
        insert into question_review_logs
          (question_id, review_decision, review_notes, knowledge_point_codes, reviewer)
        values (?, ?, ?, NULL, ?)
        """,
        (question_id, decision, note, REVIEWER),
    )


def apply_fixes(con: sqlite3.Connection) -> list[dict]:
    changed: list[dict] = []
    for (year, number), fix in QUESTION_FIXES.items():
        row = find_question(con, year, number)
        question_id = row["id"]
        old_stem = row["stem"]
        new_stem = fix.get("stem", old_stem)
        con.execute(
            """
            update questions
            set stem = ?, review_status = 'approved', source_usage = 'practice', updated_at = CURRENT_TIMESTAMP
            where id = ?
            """,
            (new_stem, question_id),
        )
        for key, text in fix.get("options", {}).items():
            con.execute(
                """
                update question_options
                set option_text = ?, updated_at = CURRENT_TIMESTAMP
                where question_id = ? and option_key = ?
                """,
                (text, question_id, key),
            )
        add_log(con, question_id, "approved", "quality_fix_applied: " + fix["note"])
        changed.append(
            {
                "action": "fixed",
                "source_year": year,
                "source_question_number": number,
                "question_id": question_id,
                "old_stem": old_stem,
                "new_stem": new_stem,
                "note": fix["note"],
            }
        )

    for (year, number), note in UNRESOLVED_ITEMS.items():
        row = find_question(con, year, number)
        question_id = row["id"]
        con.execute(
            """
            update questions
            set review_status = 'needs_review',
                source_usage = 'source_reference_only',
                updated_at = CURRENT_TIMESTAMP
            where id = ?
            """,
            (question_id,),
        )
        add_log(con, question_id, "needs_review", "needs_manual_review: " + note)
        changed.append(
            {
                "action": "moved_to_manual_review",
                "source_year": year,
                "source_question_number": number,
                "question_id": question_id,
                "old_stem": row["stem"],
                "new_stem": row["stem"],
                "note": note,
            }
        )
    return changed


def write_report(rows: list[dict]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "question_quality_auto_fixes.csv"
    columns = [
        "action",
        "source_year",
        "source_question_number",
        "question_id",
        "old_stem",
        "new_stem",
        "note",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply high-confidence question quality fixes.")
    parser.add_argument("--db", default=str(DB_PATH), help="SQLite database path.")
    parser.add_argument("--no-backup", action="store_true", help="Skip database backup.")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not args.no_backup:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"{db_path.stem}_before_question_quality_fixes_{stamp}{db_path.suffix}"
        shutil.copy2(db_path, backup_path)
        print(f"backup={backup_path}")

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    with con:
        changed = apply_fixes(con)
    report_path = write_report(changed)
    print(f"changed={len(changed)}")
    print(f"report={report_path}")


if __name__ == "__main__":
    main()
