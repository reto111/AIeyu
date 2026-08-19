from __future__ import annotations

import argparse
import json

from adaptive_profile import DEFAULT_USER_ID, connect, recalculate_profile


def main() -> None:
    parser = argparse.ArgumentParser(description="Recalculate the local learner mastery profile.")
    parser.add_argument("--user-id", type=int, default=DEFAULT_USER_ID)
    args = parser.parse_args()

    with connect() as conn:
        payload = recalculate_profile(conn, args.user_id)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
