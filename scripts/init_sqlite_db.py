from pathlib import Path
import sqlite3


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "database" / "schema.sql"
DB_PATH = ROOT / "database" / "russian_ai_tutor.sqlite"


def main() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(schema)
        conn.commit()

    print(f"Initialized database: {DB_PATH}")


if __name__ == "__main__":
    main()
