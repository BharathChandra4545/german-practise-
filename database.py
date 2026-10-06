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
DATABASE_URL = os.getenv("DATABASE_URL")
_PLACEHOLDER_VALUES = {
    "DATABASE_POSTGRES_URL",
    "DATABASE_POSTGRES_PRISMA_URL",
    "DATABASE_URL",
}


def _validated_database_url():
    value = DATABASE_URL
    if not value:
        return None
    if value in _PLACEHOLDER_VALUES or "://" not in value:
        raise RuntimeError(
            "DATABASE_URL is configured incorrectly. Set it to a PostgreSQL "
            "connection string beginning with postgresql:// or postgres://."
        )
    scheme = value.split("://", 1)[0].lower()
    if scheme not in {"postgresql", "postgres"}:
        raise RuntimeError(
            "DATABASE_URL must use the PostgreSQL connection-string format."
        )
    return value


def is_postgres():
    return _validated_database_url() is not None


def _sqlite_connection():
    connection = sqlite3.connect(SQLITE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def connect():
    database_url = _validated_database_url()
    if not database_url:
        if os.environ.get("VERCEL") or os.environ.get("FLASK_ENV") == "production":
            raise RuntimeError(
                "DATABASE_URL is required in production. Configure a PostgreSQL "
                "connection string in the deployment environment."
            )
        return _sqlite_connection()
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise RuntimeError("DATABASE_URL is set but psycopg is not installed") from exc
    return psycopg.connect(database_url, row_factory=dict_row)


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
