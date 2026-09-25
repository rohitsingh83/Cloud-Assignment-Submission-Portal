import sqlite3
import threading
from pathlib import Path
from contextlib import contextmanager
from backend.config import BASE_DIR, DATABASE_URL

DB_PATH = Path(BASE_DIR) / "assignment_portal.db"

# Thread-local storage for SQLite connections
_local = threading.local()

def get_connection():
    """Returns a thread-local SQLite connection with foreign keys and dict rows."""
    if not hasattr(_local, "connection") or _local.connection is None:
        conn = sqlite3.connect(
            str(DB_PATH),
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        _local.connection = conn
    return _local.connection

@contextmanager
def get_db_cursor():
    """Context manager for executing database transactions safely."""
    conn = get_connection()
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
    """Initializes the database schema if tables do not already exist."""
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
