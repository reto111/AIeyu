from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

from knowledge_base import connect, ensure_knowledge_base_tables


def terms_for_query(query: str) -> list[str]:
    query = query.strip()
    if not query:
        return []
    terms = [item for item in re.split(r"\s+", query) if item]
    return terms if len(terms) > 1 else [query]


def score_row(row: dict[str, Any], terms: list[str]) -> int:
    haystack = f"{row['title']}\n{row['body']}".lower()
    score = 0
    for term in terms:
        score += haystack.count(term.lower()) * 10
    if row.get("review_status") == "reviewed":
        score += 5
    return score


def search_chunks(
    query: str,
    question_type: str | None,
    knowledge_point: str | None,
    limit: int,
    reviewed_only: bool,
) -> list[dict[str, Any]]:
    filters = ["1 = 1"]
    params: list[Any] = []
    if question_type:
        filters.append("question_type_code = ?")
        params.append(question_type)
    if knowledge_point:
        filters.append("(knowledge_point_code = ? OR chunk_code = ?)")
        params.extend([knowledge_point, knowledge_point])
    if reviewed_only:
        filters.append("review_status = 'reviewed'")

    sql = f"""
        SELECT id, title, body, question_type_code, knowledge_point_code,
               chunk_code, source_locator, review_status
        FROM knowledge_chunks
        WHERE {" AND ".join(filters)}
    """
    terms = terms_for_query(query)
    with connect() as conn:
        ensure_knowledge_base_tables(conn)
        rows = [dict(row) for row in conn.execute(sql, params).fetchall()]

    scored = [(score_row(row, terms), row) for row in rows]
    if terms:
        scored = [item for item in scored if item[0] > 0]
    scored.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [
        {
            "score": score,
            "id": row["id"],
            "title": row["title"],
            "question_type_code": row["question_type_code"],
            "knowledge_point_code": row["knowledge_point_code"],
            "chunk_code": row["chunk_code"],
            "source_locator": row["source_locator"],
            "body": row["body"],
        }
        for score, row in scored[:limit]
    ]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Search local knowledge chunks for question generation context.")
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--question-type")
    parser.add_argument("--knowledge-point")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--reviewed-only", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            search_chunks(args.query, args.question_type, args.knowledge_point, args.limit, args.reviewed_only),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
