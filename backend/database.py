import os
import re
import sqlite3
import threading
from pathlib import Path
from contextlib import contextmanager
from typing import Optional
from backend.config import BASE_DIR, DATABASE_URL

DB_PATH = Path(BASE_DIR) / "assignment_portal.db"

# Thread-local storage for connections
_local = threading.local()

# Determine database engine
IS_POSTGRES = DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

def get_normalized_pg_url(url: str) -> str:
    """Ensures connection string uses postgresql:// schema."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

class PostgresCursorWrapper:
    """
    Transparent Cursor wrapper for PostgreSQL.
    Adapts SQLite '?' positional placeholders to PostgreSQL '%s' placeholders,
    allowing uniform SQL queries across both SQLite and Supabase PostgreSQL.
    """
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query: str, params=None):
        if "?" in query:
            # Replace '?' with '%s' safely for PostgreSQL
            query = query.replace("?", "%s")
        if params is not None:
            # Ensure params is a tuple/list
            if not isinstance(params, (tuple, list)):
                params = (params,)
            return self._cursor.execute(query, params)
        return self._cursor.execute(query)

    def executemany(self, query: str, seq_of_params):
        if "?" in query:
            query = query.replace("?", "%s")
        return self._cursor.executemany(query, seq_of_params)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def close(self):
        self._cursor.close()

    def __getattr__(self, name):
        return getattr(self._cursor, name)

def get_sqlite_connection():
    """Returns a thread-local SQLite connection with foreign keys and dict rows."""
    if not hasattr(_local, "sqlite_conn") or _local.sqlite_conn is None:
        conn = sqlite3.connect(
            str(DB_PATH),
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        _local.sqlite_conn = conn
    return _local.sqlite_conn

def get_postgres_connection():
    """Returns a thread-local PostgreSQL / Supabase connection."""
    import psycopg2
    from psycopg2.extras import RealDictCursor

    if not hasattr(_local, "pg_conn") or _local.pg_conn is None or _local.pg_conn.closed:
        pg_url = get_normalized_pg_url(DATABASE_URL)
        conn = psycopg2.connect(pg_url, cursor_factory=RealDictCursor)
        conn.autocommit = False
        _local.pg_conn = conn
    return _local.pg_conn

def get_connection():
    """Unified connection factory for SQLite or Supabase PostgreSQL."""
    if IS_POSTGRES:
        return get_postgres_connection()
    return get_sqlite_connection()

@contextmanager
def get_db_cursor():
    """
    Context manager for executing database transactions safely.
    Automatically manages commits, rollbacks, and cursor closure
    across SQLite and Supabase PostgreSQL.
    """
    conn = get_connection()
    if IS_POSTGRES:
        raw_cursor = conn.cursor()
        cursor = PostgresCursorWrapper(raw_cursor)
    else:
        cursor = conn.cursor()

    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()

def init_db(db_path: Path = DB_PATH):
    """
    Initializes the database schema if tables do not already exist.
    Supports both SQLite (local default) and Supabase PostgreSQL (cloud).
    """
    if IS_POSTGRES:
        conn = get_postgres_connection()
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS courses (
                course_id TEXT PRIMARY KEY,
                course_name TEXT NOT NULL,
                course_code TEXT UNIQUE NOT NULL,
                teacher_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS assignments (
                assignment_id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                deadline TEXT NOT NULL,
                max_marks INTEGER NOT NULL DEFAULT 100,
                allowed_file_types TEXT NOT NULL DEFAULT 'pdf,docx,zip',
                max_file_size_mb INTEGER NOT NULL DEFAULT 25,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS submissions (
                submission_id TEXT PRIMARY KEY,
                assignment_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_url TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL DEFAULT 0,
                submitted_at TEXT NOT NULL,
                submission_status TEXT NOT NULL DEFAULT 'SUBMITTED',
                marks REAL,
                feedback TEXT,
                graded_at TEXT,
                graded_by TEXT,
                FOREIGN KEY (assignment_id) REFERENCES assignments(assignment_id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (graded_by) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_assignments_course ON assignments(course_id);
            CREATE INDEX IF NOT EXISTS idx_submissions_assign_student ON submissions(assignment_id, student_id);
            """)
            conn.commit()
    else:
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        with conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS courses (
                course_id TEXT PRIMARY KEY,
                course_name TEXT NOT NULL,
                course_code TEXT UNIQUE NOT NULL,
                teacher_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS assignments (
                assignment_id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                deadline TEXT NOT NULL,
                max_marks INTEGER NOT NULL DEFAULT 100,
                allowed_file_types TEXT NOT NULL DEFAULT 'pdf,docx,zip',
                max_file_size_mb INTEGER NOT NULL DEFAULT 25,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS submissions (
                submission_id TEXT PRIMARY KEY,
                assignment_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_url TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL DEFAULT 0,
                submitted_at TEXT NOT NULL,
                submission_status TEXT NOT NULL DEFAULT 'SUBMITTED',
                marks REAL,
                feedback TEXT,
                graded_at TEXT,
                graded_by TEXT,
                FOREIGN KEY (assignment_id) REFERENCES assignments(assignment_id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (graded_by) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_assignments_course ON assignments(course_id);
            CREATE INDEX IF NOT EXISTS idx_submissions_assign_student ON submissions(assignment_id, student_id);
            """)
        conn.close()
