"""Database connection and portability helpers.

PostgreSQL is used whenever DATABASE_URL is configured. SQLite remains available
for local development without a database service.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE = Path(__file__).parent
SQLITE_PATH = Path(os.environ.get("GERMAN_DB_PATH", str(BASE / "german_practice.db")))


def is_postgres():
    return bool(os.environ.get("DATABASE_URL"))


def _sqlite_connection():
    connection = sqlite3.connect(SQLITE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def connect():
    if not is_postgres():
        return _sqlite_connection()
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise RuntimeError("DATABASE_URL is set but psycopg is not installed") from exc
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def placeholder_sql(sql):
    return sql.replace("?", "%s") if is_postgres() else sql


@contextmanager
def transaction():
    connection = connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

