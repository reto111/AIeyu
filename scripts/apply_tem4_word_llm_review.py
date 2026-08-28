from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "processed" / "words" / "tem4_words_review_simple.csv"
DEFAULT_OUTPUT = DEFAULT_INPUT
DEFAULT_REVIEW_ONLY = ROOT / "data" / "processed" / "words" / "tem4_words_review_only.csv"
DEFAULT_REMOVED = ROOT / "data" / "processed" / "words" / "tem4_words_removed_by_llm.csv"
DEFAULT_REPORT = ROOT / "data" / "processed" / "words" / "tem4_words_llm_review_report.json"


# These decisions are tied to the OCR page/block coordinates so that a later
# re-extraction cannot silently apply a correction to a different entry.
DECISIONS: dict[tuple[str, str], dict[str, str]] = {
    ("7", "1"): {"status": "rejected", "note": "book_heading_not_a_word"},
    ("10", "4"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("11", "2"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("11", "13"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("18", "2"): {"status": "rejected", "note": "example_sentence_not_headword"},
    ("24", "2"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("25", "10"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("27", "2"): {"word": "в", "meaning_zh": "到；往；向；在；成为；（表示数量、时间等关系）", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("34", "12"): {"word": "вид", "meaning_zh": "外貌；样子；形式；种类；（语法）体；景色，景象", "status": "approved", "note": "ocr_i_and_n_shape_correction"},
    ("45", "11"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("48", "12"): {"word": "вы", "meaning_zh": "您；你们", "status": "approved", "note": "ocr_y_shape_correction"},
    ("56", "7"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("59", "2"): {"status": "rejected", "note": "example_sentence_not_headword"},
    ("63", "4"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("70", "7"): {"status": "rejected", "note": "example_sentence_not_headword"},
    ("74", "9"): {"word": "для", "meaning_zh": "为了；给；对……来说；用于", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("75", "3"): {"word": "прикоснуться", "meaning_zh": "碰到；接触；触摸", "status": "approved", "note": "ocr_headword_recovered_from_infinitive_and_meaning"},
    ("77", "4"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("83", "13"): {"status": "rejected", "note": "example_sentence_not_headword"},
    ("87", "6"): {"word": "жизнь", "meaning_zh": "生命；生活；一生；生平", "status": "approved", "note": "ocr_headword_recovered_from_meaning"},
    ("91", "11"): {"word": "заказать", "meaning_zh": "订购；预订；定做", "status": "approved", "note": "ocr_headword_recovered_from_examples"},
    ("108", "7"): {"word": "или", "meaning_zh": "或；或者；还是；即……也……", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("108", "11"): {"status": "rejected", "note": "inflection_label_and_collocations_not_headword"},
    ("113", "3"): {"word": "их", "meaning_zh": "他们的；她们的；它们的", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("113", "7"): {"word": "к", "meaning_zh": "向；朝；往；到；对于", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("117", "5"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("118", "8"): {"word": "киоск", "meaning_zh": "售货亭；报刊亭；小摊亭", "status": "approved", "note": "ocr_b_and_g_shape_correction"},
    ("124", "15"): {"word": "коренной", "meaning_zh": "根本的；基本的；主要的；本地的（如 коренной москвич）", "status": "approved", "note": "ocr_headword_recovered_from_raw_entry"},
    ("125", "5"): {"word": "кормить", "meaning_zh": "喂养；给……吃；供养；赡养", "status": "approved", "note": "ocr_headword_recovered_from_infinitive"},
    ("130", "2"): {"status": "rejected", "note": "example_phrase_not_headword"},
    ("133", "1"): {"status": "rejected", "note": "page_number_or_layout_noise"},
    ("134", "1"): {"status": "needs_review", "note": "headword_missing_cannot_reliably_recover"},
    ("138", "2"): {"status": "rejected", "note": "fixed_expression_not_single_headword"},
    ("143", "6"): {"status": "needs_review", "note": "headword_missing_cannot_reliably_recover_from_meaning_only"},
    ("148", "2"): {"word": "мыслить", "meaning_zh": "思考；想；认为", "status": "approved", "note": "ocr_headword_recovered_from_collocations"},
    ("152", "6"): {"word": "наизусть", "meaning_zh": "熟记；背熟；凭记忆", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("154", "2"): {"remove": "true", "status": "rejected", "note": "user_confirmed_unrecoverable_ocr"},
    ("159", "3"): {"word": "по-русски", "meaning_zh": "用俄语；俄语地", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("167", "2"): {"word": "облик", "meaning_zh": "外貌；面貌；形象；景象", "status": "approved", "note": "ocr_o_and_b_shape_correction"},
    ("209", "8"): {"word": "поливать", "meaning_zh": "浇水；浇灌；（液体）洒到或冲到", "status": "approved", "note": "ocr_headword_recovered_from_raw_entry"},
    ("210", "3"): {"status": "rejected", "note": "example_sentence_not_headword"},
    ("211", "6"): {"status": "rejected", "note": "fixed_expression_not_single_headword"},
    ("211", "7"): {"status": "rejected", "note": "fragment_of_fixed_expression"},
    ("230", "11"): {"word": "разрешить", "meaning_zh": "解决；处理；允许；准许", "status": "approved", "note": "ocr_headword_recovered_from_infinitive"},
    ("234", "2"): {"status": "rejected", "note": "collocation_not_headword"},
    ("243", "2"): {"word": "раз", "meaning_zh": "一次；一回；既然；既然如此", "status": "approved", "note": "ocr_headword_recovered_from_conjunction_example"},
    ("243", "11"): {"word": "разведчик", "meaning_zh": "侦察员；侦察兵；情报员", "status": "approved", "note": "ocr_headword_recovered_from_meaning_and_example"},
    ("244", "8"): {"word": "разговаривать", "meaning_zh": "谈话；交谈；说话", "status": "approved", "note": "ocr_headword_recovered_from_infinitive"},
    ("251", "10"): {"word": "борьба", "meaning_zh": "斗争；战斗；搏斗；竞争", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("256", "2"): {"status": "rejected", "note": "fixed_expression_not_single_headword"},
    ("261", "10"): {"word": "выпустить", "meaning_zh": "放出；释放；发行；生产或出版", "status": "approved", "note": "ocr_headword_recovered_from_infinitive"},
    ("275", "7"): {"word": "собственность", "meaning_zh": "所有权；财产；所有物", "status": "approved", "note": "ocr_digit_and_latin_shape_correction"},
    ("278", "5"): {"word": "создать", "meaning_zh": "创造；创作；建立；造成", "status": "approved", "note": "ocr_headword_recovered_from_infinitive"},
    ("278", "6"): {"status": "rejected", "note": "duplicate_continuation_of_create_entry"},
    ("278", "12"): {"word": "сознательный", "meaning_zh": "有意识的；自觉的；故意的", "status": "approved", "note": "ocr_headword_recovered_from_sentence"},
    ("281", "10"): {"word": "состояние", "meaning_zh": "状态；状况；形势；心情；财产状况", "status": "approved", "note": "ocr_headword_recovered_from_meaning"},
    ("290", "3"): {"word": "стиль", "meaning_zh": "风格；文体；样式；（历法）历法", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("290", "5"): {"word": "стих", "meaning_zh": "诗；诗歌；诗句", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("290", "8"): {"word": "стоить", "meaning_zh": "值；花费；值得", "status": "approved", "note": "ocr_headword_confirmed_from_conjugation"},
    ("293", "16"): {"word": "стул", "meaning_zh": "椅子；凳子", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("295", "1"): {"status": "rejected", "note": "page_number_or_layout_noise"},
    ("298", "9"): {"word": "танец", "meaning_zh": "舞蹈；舞；舞会（复数 танцы）", "status": "approved", "note": "ocr_headword_recovered_from_collocations"},
    ("307", "9"): {"word": "требовать", "meaning_zh": "要求；需要；索要；召唤", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("314", "11"): {"word": "удобство", "meaning_zh": "舒适；方便；便利；方便设施", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("315", "1"): {"status": "rejected", "note": "page_number_or_layout_noise"},
    ("315", "11"): {"word": "узкий", "meaning_zh": "狭窄的；窄的；有限的；狭义的", "status": "approved", "note": "ocr_headword_recovered_from_definition"},
    ("325", "13"): {"word": "форма", "meaning_zh": "形式；形状；制服；表格", "status": "approved", "note": "ocr_headword_recovered_from_collocations"},
    ("326", "6"): {"word": "фронт", "meaning_zh": "前线；战线；统一战线；（转）活动领域", "status": "approved", "note": "ocr_headword_confirmed_from_raw_entry"},
    ("332", "2"): {"status": "needs_review", "note": "multiple_entries_merged_headword_missing"},
    ("340", "1"): {"status": "rejected", "note": "page_number_or_layout_noise"},
    ("342", "3"): {"word": "экономия", "meaning_zh": "节约；节省；节约的办法；经济（学）", "status": "approved", "note": "ocr_o_and_b_shape_correction"},
    ("346", "10"): {"word": "отложить", "meaning_zh": "推迟；延期；搁置；把……放到一边", "status": "approved", "note": "ocr_headword_recovered_from_infinitive"},
    ("350", "1"): {"word": "капля в море", "part_of_speech": "固定结构", "meaning_zh": "沧海一粟；微不足道的一小部分", "status": "approved", "note": "ocr_b_to_v_and_m6pe_to_more_recovered_from_idiom"},
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply local LLM review decisions to TEM4 OCR vocabulary.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--review-only", type=Path, default=DEFAULT_REVIEW_ONLY)
    parser.add_argument("--removed", type=Path, default=DEFAULT_REMOVED)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    fieldnames = list(rows[0]) if rows else []
    counts = {"approved": 0, "rejected": 0, "needs_review": 0, "not_found": 0}
    report: list[dict[str, str]] = []
    removed_rows: list[dict[str, str]] = []
    output_rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for row in rows:
        key = ((row.get("source_page") or "").strip(), (row.get("block_index") or "").strip())
        decision = DECISIONS.get(key)
        if decision is None:
            output_rows.append(row)
            continue
        seen.add(key)
        old_word = row.get("word", "")
        old_meaning = row.get("meaning_zh", "")
        if decision.get("remove") == "true":
            counts["rejected"] += 1
            counts["removed"] = counts.get("removed", 0) + 1
            removed = dict(row)
            removed["remove_reason"] = decision.get("note", "")
            removed_rows.append(removed)
            report.append(
                {
                    "source_page": key[0],
                    "block_index": key[1],
                    "old_word": old_word,
                    "new_word": "",
                    "old_meaning_zh": old_meaning,
                    "new_meaning_zh": "",
                    "status": "removed",
                    "note": decision.get("note", ""),
                }
            )
            continue
        if decision.get("word"):
            row["word"] = decision["word"]
        if decision.get("meaning_zh"):
            row["meaning_zh"] = decision["meaning_zh"]
        if decision.get("part_of_speech"):
            row["part_of_speech"] = decision["part_of_speech"]
        row["review_status"] = decision["status"]
        row["review_notes"] = ";".join(
            item for item in [row.get("review_notes", ""), "local_llm_review", decision.get("note", "")] if item
        )
        counts[decision["status"]] += 1
        report.append(
            {
                "source_page": key[0],
                "block_index": key[1],
                "old_word": old_word,
                "new_word": row.get("word", ""),
                "old_meaning_zh": old_meaning,
                "new_meaning_zh": row.get("meaning_zh", ""),
                "status": decision["status"],
                "note": decision.get("note", ""),
            }
        )
        output_rows.append(row)

    missing = sorted(set(DECISIONS) - seen)
    counts["not_found"] = len(missing)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_rows)
    args.review_only.parent.mkdir(parents=True, exist_ok=True)
    with args.review_only.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(row for row in output_rows if row.get("review_status") == "needs_review")
    args.removed.parent.mkdir(parents=True, exist_ok=True)
    removed_fields = fieldnames + (["remove_reason"] if "remove_reason" not in fieldnames else [])
    with args.removed.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=removed_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(removed_rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({"counts": counts, "missing_keys": missing, "rows": report}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
