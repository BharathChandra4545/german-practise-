"""Create all persistent tables.

Usage:
    DATABASE_URL=postgresql://... python init_db.py
f"""
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
                        f"""
                        DO $$
                        DECLARE constraint_name TEXT;
                        BEGIN
                            FOR constraint_name IN
                                SELECT conname
                                FROM pg_constraint
                                WHERE conrelid = '{table}'::regclass AND contype = 'c'
                            LOOP
                                EXECUTE format(
                                    'ALTER TABLE %I DROP CONSTRAINT %I',
                                    '{table}', constraint_name
                                );
                            END LOOP;
                        END $$;
                        """,
                    )
        else:
            connection.executescript(script)
        connection.commit()
    print(f"Initialized {'PostgreSQL' if is_postgres() else 'SQLite'} using {schema_path}")


if __name__ == "__main__":
    main()
