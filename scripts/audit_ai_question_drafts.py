from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"
PAYLOAD_SIMILARITY_THRESHOLD = 0.74


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def similarity_ratio(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_text(left), normalize_text(right)).ratio()


def years_in_text(text: str) -> set[str]:
    return set(re.findall(r"(?:1[0-9]{3}|20[0-9]{2})", text))


def culture_key_terms(text: str) -> set[str]:
    terms = [
        "莫斯科",
        "首都",
        "克里姆林宫",
        "红场",
        "苏联",
        "俄罗斯",
        "总统",
        "官邸",
        "炮王",
        "钟王",
        "莫斯科大学",
        "圣彼得堡",
        "成立",
        "迁都",
        "联邦",
    ]
    return {term for term in terms if term in text}


def is_same_culture_signature(left: str, right: str) -> bool:
    shared_years = years_in_text(left) & years_in_text(right)
    shared_terms = culture_key_terms(left) & culture_key_terms(right)
    return len(shared_years) >= 2 and len(shared_terms) >= 2


def question_payload(question: dict[str, Any]) -> str:
    return "\n".join(
        [
            str(question.get("stem") or ""),
            *[str(text) for text in question.get("options", [])],
            str(question.get("explanation_zh") or ""),
        ]
    )


def fetch_ai_drafts(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    question_rows = conn.execute(
        """
        SELECT
          q.id,
          q.stem,
          q.explanation_zh,
          q.difficulty,
          q.review_status,
          q.generation_status,
          q.similarity_review_status,
          qt.code AS question_type
        FROM questions q
        JOIN question_types qt ON qt.id = q.question_type_id
        WHERE q.content_origin = 'ai_generated'
          AND q.generation_status = 'ai_draft'
          AND q.review_status = 'needs_review'
        ORDER BY q.id
        """
    ).fetchall()
    option_rows = conn.execute(
        """
        SELECT question_id, option_key, option_text
        FROM question_options
        WHERE question_id IN (
          SELECT id
          FROM questions
          WHERE content_origin = 'ai_generated'
            AND generation_status = 'ai_draft'
            AND review_status = 'needs_review'
        )
        ORDER BY question_id, option_key
        """
    ).fetchall()
    options_by_question: dict[int, list[str]] = {}
    for row in option_rows:
        options_by_question.setdefault(int(row["question_id"]), []).append(str(row["option_text"] or ""))

    return [
        {
            "id": int(row["id"]),
            "stem": str(row["stem"] or ""),
            "explanation_zh": str(row["explanation_zh"] or ""),
            "difficulty": int(row["difficulty"] or 0),
            "review_status": row["review_status"],
            "generation_status": row["generation_status"],
            "similarity_review_status": row["similarity_review_status"],
            "question_type": row["question_type"],
            "options": options_by_question.get(int(row["id"]), []),
        }
        for row in question_rows
    ]


def culture_depth_risks(question: dict[str, Any]) -> list[str]:
    if question["question_type"] != "culture_choice" or question["difficulty"] < 4:
        return []
    stem = question["stem"]
    text = question_payload(question)
    years = years_in_text(text)
    depth_markers = [
        "时间",
        "时期",
        "背景",
        "关系",
        "原因",
        "制度",
        "事件",
        "成立",
        "成为",
        "混淆",
        "对应",
        "节点",
        "历史",
        "综合",
        "组合",
        "判断",
        "描述",
        "特征",
        "流向",
        "水量",
        "别称",
        "分布",
        "产地",
        "资源",
    ]
    low_depth_patterns = [
        "名称是什么",
        "叫什么",
        "位于哪里",
        "哪一项是正确的",
        "哪一项正确",
        "下列关于",
    ]
    stem_marker_count = sum(1 for marker in depth_markers if marker in stem)
    if any(pattern in stem for pattern in low_depth_patterns) and len(years) < 2 and stem_marker_count < 2:
        return ["culture difficulty=4 may be too shallow; looks like single fact/name/location recall."]
    return []


def audit() -> list[dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        questions = fetch_ai_drafts(conn)

    results: list[dict[str, Any]] = []
    for question in questions:
        risks = culture_depth_risks(question)
        closest: dict[str, Any] | None = None
        for other in questions:
            if other["id"] >= question["id"]:
                continue
            ratio = similarity_ratio(question_payload(question), question_payload(other))
            same_signature = (
                question["question_type"] == "culture_choice"
                and other["question_type"] == "culture_choice"
                and is_same_culture_signature(question_payload(question), question_payload(other))
            )
            if closest is None or ratio > closest["ratio"] or same_signature:
                closest = {"question_id": other["id"], "ratio": ratio, "same_culture_signature": same_signature}
        if closest and (closest["ratio"] >= PAYLOAD_SIMILARITY_THRESHOLD or closest["same_culture_signature"]):
            risks.append(
                f"too similar to AI draft {closest['question_id']} "
                f"(payload_ratio={closest['ratio']:.2f}, "
                f"same_culture_signature={closest['same_culture_signature']})."
            )

        results.append(
            {
                "question_id": question["id"],
                "question_type": question["question_type"],
                "difficulty": question["difficulty"],
                "stem": question["stem"],
                "closest_ai_draft": closest,
                "risks": risks,
                "recommended_decision": "needs_fix" if risks else "review_manually",
            }
        )
    return results


def persist_flags(results: list[dict[str, Any]]) -> dict[str, int]:
    flagged = [item for item in results if item["risks"]]
    with sqlite3.connect(DB_PATH) as conn:
        for item in flagged:
            conn.execute(
                """
                UPDATE questions
                SET similarity_review_status = 'flagged',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (item["question_id"],),
            )
            conn.execute(
                """
                INSERT INTO question_review_logs (
                  question_id, review_decision, review_notes, reviewer
                )
                VALUES (?, 'needs_fix', ?, 'ai_quality_audit')
                """,
                (item["question_id"], "；".join(item["risks"])),
            )
        conn.commit()
    return {"flagged": len(flagged), "checked": len(results)}


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Audit AI-generated question drafts for duplicate and depth risks.")
    parser.add_argument("--persist-flags", action="store_true", help="Mark risky questions as similarity_review_status=flagged and log needs_fix.")
    args = parser.parse_args()

    results = audit()
    output: dict[str, Any] = {"checked": len(results), "results": results}
    if args.persist_flags:
        output["persisted"] = persist_flags(results)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
