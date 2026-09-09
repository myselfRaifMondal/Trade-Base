"""SQLite schema management for the Trade Base application.

The application database (``users.db``) is created locally on first run and is
deliberately not tracked in version control, so every clone starts from a clean
schema instead of inheriting another developer's trades.
"""

import sqlite3

DB_PATH = "users.db"

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS trades (
        username TEXT,
        symbol TEXT,
        action TEXT,
        quantity INTEGER,
        price REAL,
        timestamp TEXT
    )
    """,
)


def get_connection(db_path=DB_PATH):
    """Return a connection to the application database."""
    return sqlite3.connect(db_path)


def init_db(db_path=DB_PATH):
    """Create the ``users`` and ``trades`` tables if they do not already exist.

    Safe to call on every start-up: each statement uses ``IF NOT EXISTS``, so an
    existing database is left untouched.
    """
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        for statement in SCHEMA:
            cursor.execute(statement)
        conn.commit()
    finally:
        conn.close()


def ensure_user(username, db_path=DB_PATH):
    """Register ``username`` in the ``users`` table if it is not there already.

    This is what makes a trader visible on the leaderboard, which is driven by
    ``SELECT username FROM users``. It is idempotent: calling it on every run
    with the same name leaves exactly one row. No password is stored - this is a
    paper-trading demo with no authentication.

    Returns the normalised username, or ``None`` if the name was blank.
    """
    username = (username or "").strip()
    if not username:
        return None
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO users (username) VALUES (?)", (username,)
        )
        conn.commit()
    finally:
        conn.close()
    return username


if __name__ == "__main__":
    init_db()
    print(f"Initialised {DB_PATH}")
