"""Copy existing local SQLite data into DATABASE_URL PostgreSQL.

Usage:
    $env:DATABASE_URL = "postgresql://..."
    py migrate_sqlite_to_postgres.py
"""
import os
import sqlite3
from pathlib import Path

from database import connect, placeholder_sql
from init_db import main as init_db


def main():
    database_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_POSTGRES_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    source = Path(os.environ.get("GERMAN_DB_PATH", str(Path(__file__).parent / "german_practice.db")))
    if not source.exists():
        raise FileNotFoundError(f"SQLite database not found: {source}")

    init_db()
    sqlite_connection = sqlite3.connect(source)
    sqlite_connection.row_factory = sqlite3.Row
    postgres_connection = connect()
    try:
        for row in sqlite_connection.execute("SELECT * FROM vocabulary ORDER BY id"):
            postgres_connection.execute(placeholder_sql("""
                INSERT INTO vocabulary
                    (id, german, english, article, pronunciation, plural, level, topic, example_de, example_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO NOTHING
            """), tuple(row))
        for row in sqlite_connection.execute(
            "SELECT vocab_id, correct, created_at FROM attempts ORDER BY id"
        ):
            postgres_connection.execute(placeholder_sql("""
                INSERT INTO attempts (vocab_id, correct, created_at)
                VALUES (?, ?, ?)
            """), tuple(row))
        postgres_connection.commit()
    except Exception:
        postgres_connection.rollback()
        raise
    finally:
        sqlite_connection.close()
        postgres_connection.close()
    print(f"Migrated {source} into PostgreSQL.")


if __name__ == "__main__":
    main()
