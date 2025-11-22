# db.py
import sqlite3
import pandas as pd
import os
import io
from typing import Optional, List, Tuple

DB_FILE = os.path.join(os.path.dirname(__file__), 'datasets.db')

CREATE_TABLE_SQL = '''
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

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute(CREATE_TABLE_SQL)
    conn.execute(CREATE_INDEX_SQL)
    conn.commit()
    return conn

def save_dataset(name: str, df: pd.DataFrame, user_id: int) -> None:
    """Save dataset for a specific user"""
    conn = get_connection()
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    cur = conn.cursor()
    # Use REPLACE to allow overwriting datasets with the same name for the same user
    cur.execute('INSERT OR REPLACE INTO datasets (name, csv, user_id) VALUES (?, ?, ?)', 
               (name, csv_bytes, user_id))
    conn.commit()
    conn.close()

def list_datasets(user_id: int) -> List[Tuple[int, str, str]]:
    """List all datasets for a specific user"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name, uploaded_at FROM datasets WHERE user_id=? ORDER BY uploaded_at DESC', 
               (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def load_dataset(name: str, user_id: int) -> Optional[pd.DataFrame]:
    """Load a specific dataset for a user"""
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
    """Delete a specific dataset for a user"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM datasets WHERE name=? AND user_id=?', (name, user_id))
    conn.commit()
    conn.close()

def count_user_datasets(user_id: int) -> int:
    """Count total datasets for a user"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM datasets WHERE user_id=?', (user_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count