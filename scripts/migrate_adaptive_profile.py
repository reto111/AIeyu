from __future__ import annotations

import json

from adaptive_profile import (
    DEFAULT_USER_ID,
    backfill_default_user,
    connect,
    ensure_adaptive_tables,
    ensure_default_user,
    rebuild_question_exposures,
    recalculate_profile,
)


def main() -> None:
    with connect() as conn:
        ensure_adaptive_tables(conn)
        user_id = ensure_default_user(conn)
        backfill_default_user(conn, user_id)
        rebuild_question_exposures(conn, user_id)
        profile = recalculate_profile(conn, DEFAULT_USER_ID)
    print(
        json.dumps(
            {
                "status": "ok",
                "default_user_id": DEFAULT_USER_ID,
                "question_type_count": len(profile["question_type_mastery"]),
                "knowledge_count": len(profile["knowledge_mastery"]),
                "top_weaknesses": profile["top_weaknesses"],
                "next_training": profile["next_training"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
