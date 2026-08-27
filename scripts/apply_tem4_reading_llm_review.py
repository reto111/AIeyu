from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"

STEM_FIXES = {
    (2017, 72): "Почему Санька дал Женьке своё снаряжение?",
    (2017, 73): "Когда команда узнала, что вратарём будет Женька?",
    (2017, 76): "Почему гостю не следует стремиться быть особенно точным?",
    (2017, 78): "Почему автор предлагает позаботиться о цветах заранее?",
    (2018, 74): "Почему Коля не открыл Свете дверь лаборатории?",
    (2018, 76): "Почему брат автора уехал во Францию?",
    (2018, 77): "Во что верила мать автора?",
    (2019, 82): "Что произошло в жизни Баталова, когда ему было четырнадцать лет?",
    (2019, 83): "Где жил Баталов в годы Великой Отечественной войны?",
    (2019, 86): "Как понять предложение «Этот дуб видел Пушкина, который гулял по бульвару»?",
    (2019, 90): "На чьи деньги создали памятник Пушкину?",
    (2021, 71): "Какое событие помогло В.В. Андрееву найти дело всей жизни?",
    (2021, 72): "За сколько времени В.В. Андреев научился играть на балалайке?",
    (2021, 73): "Почему критика называла В.В. Андреева «отцом балалайки»?",
    (2021, 74): "В каком году был основан Оркестр народных инструментов имени В.В. Андреева?",
    (2021, 75): "О чём мечтал В.В. Андреев?",
    (2022, 74): "Где Лёва замечательно отдохнул?",
    (2022, 80): "Почему химический элемент № 104 называется Курчатовием?",
    (2023, 90): "Какие журналы получили бурное развитие в 70-е годы XVIII века?",
}

OPTION_FIXES = {
    (2018, 75, "B"): "Коля не смог достать Свете звезду.",
    (2018, 77, "D"): "Если видишь паука, будет хорошая новость.",
    (2019, 76, "B"): "На острове в океане.",
    (2019, 76, "D"): "В деревне на берегу моря.",
    (2019, 85, "D"): "«Мать».",
    (2019, 89, "B"): "В начале Тверского бульвара.",
    (2019, 89, "C"): "На Москворецкой набережной.",
    (2019, 90, "A"): "На деньги народа.",
    (2019, 90, "B"): "На деньги государства.",
    (2019, 90, "C"): "На деньги Екатерины II.",
    (2019, 90, "D"): "На деньги семьи Пушкиных.",
    (2018, 80, "B"): "Незнакомые добрые люди.",
    (2018, 80, "C"): "Люди, которые верили в приметы.",
    (2018, 80, "D"): "Люди, которые путешествовали по Франции.",
    (2018, 90, "B"): "Он считает, что жизнь заключается в движении.",
    (2018, 90, "D"): "Он считает, что в здоровом теле должен быть здоровый дух.",
    (2022, 90, "D"): "Пиво и воду с мёдом.",
    (2017, 90, "D"): "Вавилов - учёный с широкими научными интересами.",
    (2021, 90, "D"): "Он стал самостоятельным международным видом спорта.",
    (2021, 72, "B"): "За 7 дней.",
    (2021, 73, "B"): "Он создал первую школу балалайки для детей.",
    (2021, 73, "D"): "Он усовершенствовал балалайку и виртуозно на ней играл.",
    (2021, 75, "B"): "О том, чтобы его оркестр гастролировал по всему миру.",
    (2023, 90, "D"): "Сатирические.",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply high-confidence local-model corrections to TEM4 reading text.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    backup = args.db.parent.parent / "data" / "processed" / "backups" / (
        "russian_ai_tutor_before_tem4_reading_review_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".sqlite"
    )
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.db, backup)
    changed = []
    with sqlite3.connect(args.db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT q.id,q.source_year,q.source_question_number,q.stem,p.id AS passage_id,p.body
               FROM questions q JOIN exam_systems e ON e.id=q.exam_system_id
               JOIN question_types t ON t.id=q.question_type_id LEFT JOIN passages p ON p.id=q.passage_id
               WHERE e.code='TEM4_RU' AND t.code='reading_choice'"""
        ).fetchall()
        for row in rows:
            key = (int(row["source_year"]), int(row["source_question_number"]))
            fields = []
            if key in STEM_FIXES and row["stem"] != STEM_FIXES[key]:
                conn.execute("UPDATE questions SET stem=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (STEM_FIXES[key], row["id"]))
                fields.append("stem")
            if row["passage_id"] and row["body"]:
                body = re.sub(r"(?mi)^\s*--- Page[^\n]*---\s*$", "", row["body"])
                body = body.replace("沙拉俄语", "")
                body = body.replace("тихо в ел из дома", "тихо вышел из дома")
                body = body.replace("Taм", "Там").replace("Bce", "Все")
                body = body.replace("Haроду", "Народу").replace("Tвepcкoй", "Тверской")
                body = body.replace("кaк", "как")
                body = re.sub(r"\n{3,}", "\n\n", body).strip()
                if body != row["body"]:
                    conn.execute("UPDATE passages SET body=? WHERE id=?", (body, row["passage_id"]))
                    fields.append("passage_body")
            for (year, number, option_key), text in OPTION_FIXES.items():
                if (year, number) != key:
                    continue
                option = conn.execute("SELECT id FROM question_options WHERE question_id=? AND option_key=?", (row["id"], option_key)).fetchone()
                if option:
                    conn.execute("UPDATE question_options SET option_text=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (text, option[0]))
                else:
                    conn.execute("INSERT INTO question_options(question_id,option_key,option_text,sort_order) VALUES(?,?,?,?)", (row["id"], option_key, text, ord(option_key) - ord("A")))
                fields.append("option_" + option_key)
            if fields:
                conn.execute("INSERT INTO question_review_logs(question_id,review_decision,review_notes,reviewer) VALUES(?,?,?,?)", (row["id"], "needs_review", "reading_local_llm_cross_check; changed=" + ",".join(dict.fromkeys(fields)), "local_llm_reading_review"))
                changed.append({"year": key[0], "question": key[1], "fields": list(dict.fromkeys(fields))})
        if args.dry_run:
            conn.rollback()
        else:
            conn.commit()
    print({"dry_run": args.dry_run, "backup": str(backup), "changed": changed, "changed_count": len(changed)})


if __name__ == "__main__":
    main()
