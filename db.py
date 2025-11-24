# db.py
import sqlite3
import pandas as pd
import os
import io
import hashlib
from typing import Optional, List, Tuple

DB_FILE = os.path.join(os.path.dirname(__file__), "datasets.db")

CREATE_USERS_SQL = '''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

CREATE_DATASETS_SQL = '''
CREATE TABLE IF NOT EXISTS datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    csv BLOB,
    user_id INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, user_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
'''

CREATE_INDEX_SQL = '''
CREATE INDEX IF NOT EXISTS idx_datasets_user_id ON datasets(user_id);
'''

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _ensure_users_table(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute(CREATE_USERS_SQL)
    conn.commit()
    # ensure default admin exists
    cur.execute('SELECT id FROM users WHERE username=?', (DEFAULT_ADMIN_USERNAME,))
    if cur.fetchone() is None:
        cur.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (DEFAULT_ADMIN_USERNAME, _hash_password(DEFAULT_ADMIN_PASSWORD))
        )
        conn.commit()

def _datasets_table_has_user_id(conn: sqlite3.Connection) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='datasets'")
    if cur.fetchone() is None:
        return False
    cur.execute("PRAGMA table_info(datasets);")
    cols = [row[1] for row in cur.fetchall()]
    return 'user_id' in cols

def _recreate_datasets_table(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS datasets;")
    cur.execute(CREATE_DATASETS_SQL)
    cur.execute(CREATE_INDEX_SQL)
    conn.commit()

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    # ensure users table and default admin
    _ensure_users_table(conn)
    # if datasets table missing or lacking user_id, (re)create it cleanly
    if not _datasets_table_has_user_id(conn):
        _recreate_datasets_table(conn)
    return conn

def save_dataset(name: str, df: pd.DataFrame, user_id: int) -> None:
    conn = get_connection()
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    cur = conn.cursor()
    cur.execute(
        'INSERT OR REPLACE INTO datasets (name, csv, user_id) VALUES (?, ?, ?)',
        (name, csv_bytes, user_id)
    )
    conn.commit()
    conn.close()

def list_datasets(user_id: int) -> List[Tuple[int, str, str]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name, uploaded_at FROM datasets WHERE user_id=? ORDER BY uploaded_at DESC', (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def load_dataset(name: str, user_id: int) -> Optional[pd.DataFrame]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT csv FROM datasets WHERE name=? AND user_id=?', (name, user_id))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        csv_bytes = row[0]
        return pd.read_csv(io.BytesIO(csv_bytes))
    return None

def delete_dataset(name: str, user_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM datasets WHERE name=? AND user_id=?', (name, user_id))
    conn.commit()
    conn.close()

def count_user_datasets(user_id: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM datasets WHERE user_id=?', (user_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count