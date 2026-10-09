"""Small parameterised SQLite functions, independent of Streamlit."""
import sqlite3
import uuid
from datetime import datetime, timezone
from config import DB_PATH, UPLOAD_DIR, CATEGORIES, SEVERITIES, STATUSES, STRING_LIMITS

def connect() -> sqlite3.Connection:
    """Open a short-lived connection with dictionary-like rows and foreign keys."""
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

def timestamp() -> str:
    """Use timezone-aware ISO timestamps so history has unambiguous times."""
    return datetime.now(timezone.utc).isoformat()

def init_db() -> None:
    """Create runtime folders and tables without deleting existing reports."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    connection = connect()
    try:
        with connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS complaints (
                    id TEXT PRIMARY KEY, category TEXT NOT NULL, title TEXT NOT NULL,
                    description TEXT NOT NULL, location TEXT NOT NULL, image_path TEXT NOT NULL,
                    severity TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Submitted',
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    notes TEXT, needs_review INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    complaint_id TEXT NOT NULL REFERENCES complaints(id),
                    status TEXT NOT NULL, changed_at TEXT NOT NULL
                );
            """)
    finally:
        connection.close()

def normalize_id(complaint_id: str) -> str:
    """Make pasted tracking IDs forgiving about spaces and letter case."""
    return complaint_id.strip().upper()

def save_complaint(data: dict) -> str:
    """Validate citizen edits and insert the report and initial history atomically."""
    if data.get('category') not in CATEGORIES or data.get('severity') not in SEVERITIES:
        raise ValueError("Please choose a valid category and severity.")
    for field, limit in {'title':80, 'description':2000, 'location':300}.items():
        value = data.get(field)
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
            raise ValueError("Please enter a valid " + field + ".")
    if len(data.get('notes', '') or '') > 1000:
        raise ValueError("Please keep notes under 1000 characters.")
    path = data.get('image_path', '')
    # Only a generated filename inside uploads may be stored.
    if not isinstance(path, str) or not path.startswith('uploads/') or '/' in path[8:] or '\\' in path or '..' in path:
        raise ValueError("Please upload an image before submitting.")
    connection = connect()
    try:
        with connection:
            now = timestamp()
            # A primary-key collision is retried; uniqueness is enforced by SQLite.
            for attempt in range(20):
                complaint_id = 'CE-' + uuid.uuid4().hex[:8].upper()
                cursor = connection.execute("""INSERT OR IGNORE INTO complaints
                    (id, category, title, description, location, image_path, severity,
                    status, created_at, updated_at, notes, needs_review)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (complaint_id, data['category'], data['title'].strip(), data['description'].strip(),
                     data['location'].strip(), path, data['severity'], 'Submitted', now, now,
                     data.get('notes', ''), int(bool(data.get('needs_review', False)))))
                if cursor.rowcount:
                    connection.execute("INSERT INTO status_history (complaint_id, status, changed_at) VALUES (?, ?, ?)",
                                       (complaint_id, 'Submitted', now))
                    return complaint_id
            raise RuntimeError("Could not allocate an ID. Please retry.")
    finally:
        connection.close()

def get_complaint(complaint_id: str) -> dict | None:
    """Look up one saved complaint without exposing SQL construction to callers."""
    connection = connect()
    try:
        row = connection.execute("SELECT * FROM complaints WHERE id = ?", (normalize_id(complaint_id),)).fetchone()
        return dict(row) if row else None
    finally:
        connection.close()

def list_complaints(status: str | None = None, category: str | None = None) -> list[dict]:
    """Filter with bound values, keeping the query constant and easy to audit."""
    connection = connect()
    try:
        rows = connection.execute("""SELECT * FROM complaints
            WHERE (? IS NULL OR status = ?) AND (? IS NULL OR category = ?)
            ORDER BY created_at DESC""", (status, status, category, category)).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()

def update_status(complaint_id: str, status: str) -> None:
    """Advance one step and save history in the same transaction."""
    if status not in STATUSES:
        raise ValueError("Please choose a valid status.")
    connection = connect()
    try:
        with connection:
            complaint_id = normalize_id(complaint_id)
            row = connection.execute("SELECT status FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
            if not row:
                raise ValueError("Complaint not found.")
            current = row['status']
            if status == current:
                return
            if STATUSES.index(status) != STATUSES.index(current) + 1:
                raise ValueError("Move from Submitted to In Progress, then to Resolved.")
            now = timestamp()
            connection.execute("UPDATE complaints SET status = ?, updated_at = ? WHERE id = ?", (status, now, complaint_id))
            connection.execute("INSERT INTO status_history (complaint_id, status, changed_at) VALUES (?, ?, ?)",
                               (complaint_id, status, now))
    finally:
        connection.close()

def get_history(complaint_id: str) -> list[dict]:
    """Return the status timeline in insertion order, including initial submission."""
    connection = connect()
    try:
        rows = connection.execute("SELECT * FROM status_history WHERE complaint_id = ? ORDER BY id", (normalize_id(complaint_id),)).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
