# auth.py
import sqlite3
import hashlib
import os
from typing import Optional, Tuple

DB_FILE = os.path.join(os.path.dirname(__file__), 'datasets.db')

CREATE_USERS_TABLE = '''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute(CREATE_USERS_TABLE)
    conn.commit()
    return conn

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, password: str) -> Tuple[bool, str]:
    """
    Create a new user account
    Returns: (success: bool, message: str)
    """
    if not username or not password:
        return False, "Username and password cannot be empty"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        password_hash = hash_password(password)
        cur.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                   (username, password_hash))
        conn.commit()
        conn.close()
        return True, "Account created successfully"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    except Exception as e:
        return False, f"Error creating account: {str(e)}"

def verify_user(username: str, password: str) -> Tuple[bool, Optional[int]]:
    """
    Verify user credentials
    Returns: (authenticated: bool, user_id: Optional[int])
    """
    if not username or not password:
        return False, None
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        password_hash = hash_password(password)
        cur.execute('SELECT id FROM users WHERE username=? AND password_hash=?', 
                   (username, password_hash))
        row = cur.fetchone()
        conn.close()
        
        if row:
            return True, row[0]
        return False, None
    except Exception as e:
        print(f"Error verifying user: {e}")
        return False, None

def get_user_id(username: str) -> Optional[int]:
    """Get user ID from username"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE username=?', (username,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None