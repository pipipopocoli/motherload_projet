"""
Database models and initialization for Librarium.
"""

import sqlite3
from pathlib import Path

from motherload_projet.library.paths import bibliotheque_root, ensure_dir


DB_NAME = "librarium.db"


def get_db_path() -> Path:
    """Returns the path to the SQLite database."""
    # Use local project path to avoid permissions issues on Desktop
    root = Path(__file__).resolve().parent.parent / "data"
    ensure_dir(root)
    return root / DB_NAME

def get_connection() -> sqlite3.Connection:
    """Establishes a connection to the SQLite database."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initializes the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Enable foreign keys
    
    # Papers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doi TEXT UNIQUE NOT NULL,
        title TEXT,
        year INTEGER,
        abstract TEXT,
        journal TEXT,
        volume TEXT,
        issue TEXT,
        pages TEXT,
        publisher TEXT,
        pdf_path TEXT,
        file_hash TEXT,
        url TEXT,
        added_at TEXT,
        source TEXT,
        status TEXT,
        type TEXT,
        is_oa TEXT,
        oa_status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Authors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)

    # Paper_Authors Junction Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paper_authors (
        paper_id INTEGER,
        author_id INTEGER,
        PRIMARY KEY (paper_id, author_id),
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
    );
    """)

    # Collections Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)

    # Paper_Collections Junction Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paper_collections (
        paper_id INTEGER,
        collection_id INTEGER,
        PRIMARY KEY (paper_id, collection_id),
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
        FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
    );
    """)

    # Tags Table (for keywords)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)

    # Paper_Tags Junction Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paper_tags (
        paper_id INTEGER,
        tag_id INTEGER,
        PRIMARY KEY (paper_id, tag_id),
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized at {get_db_path()}")

if __name__ == "__main__":
    init_db()
