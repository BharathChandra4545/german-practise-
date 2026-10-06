"""Create all persistent tables.

Usage:
    DATABASE_URL=postgresql://... python init_db.py
"""
import os
from pathlib import Path

from database import connect, is_postgres


def main():
    schema_path = Path(__file__).parent / "database" / (
        "schema.sql" if is_postgres() else "schema_sqlite.sql"
    )
    script = schema_path.read_text(encoding="utf-8")
    with connect() as connection:
        if is_postgres():
            with connection.cursor() as cursor:
                cursor.execute(script)
                for table in ("topics", "words", "vocabulary"):
                    cursor.execute(
                        f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS "
                        f"{table}_level_check"
                    )
                    cursor.execute(
                        f"ALTER TABLE {table} ADD CONSTRAINT {table}_level_check "
                        "CHECK (level IN ('A1', 'A2'))"
                    )
        else:
            connection.executescript(script)
        connection.commit()
    print(f"Initialized {'PostgreSQL' if is_postgres() else 'SQLite'} using {schema_path}")


if __name__ == "__main__":
    main()
