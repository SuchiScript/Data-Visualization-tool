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
    name TEXT UNIQUE,
    csv BLOB,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    return conn

def save_dataset(name: str, df: pd.DataFrame) -> None:
    conn = get_connection()
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    cur = conn.cursor()
    # Use REPLACE INTO to allow overwriting same name
    cur.execute('INSERT OR REPLACE INTO datasets (name, csv) VALUES (?, ?)', (name, csv_bytes))
    conn.commit()
    conn.close()

def list_datasets() -> List[Tuple[int, str, str]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name, uploaded_at FROM datasets ORDER BY uploaded_at DESC')
    rows = cur.fetchall()
    conn.close()
    return rows

def load_dataset(name: str) -> Optional[pd.DataFrame]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT csv FROM datasets WHERE name=?', (name,))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        csv_bytes = row[0]
        return pd.read_csv(io.BytesIO(csv_bytes))
    return None

def delete_dataset(name: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM datasets WHERE name=?', (name,))
    conn.commit()
    conn.close()
