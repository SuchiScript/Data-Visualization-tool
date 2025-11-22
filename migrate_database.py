# migrate_database.py
"""
Migration script to update existing database schema
Run this once to add user authentication to existing database
"""
import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'datasets.db')

def migrate():
    print("Starting database migration...")
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Check if users table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    users_table_exists = cur.fetchone() is not None
    
    if not users_table_exists:
        print("Creating users table...")
        cur.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create a default admin user (password: admin123)
        # Hash for 'admin123'
        default_hash = '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9'
        cur.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                   ('admin', default_hash))
        print("Created default user: admin / admin123")
    
    # Check if datasets table has user_id column
    cur.execute("PRAGMA table_info(datasets)")
    columns = [row[1] for row in cur.fetchall()]
    
    if 'user_id' not in columns:
        print("Adding user_id column to datasets table...")
        
        # Get the admin user ID
        cur.execute("SELECT id FROM users WHERE username='admin'")
        admin_id = cur.fetchone()[0]
        
        # Add user_id column with default value
        cur.execute(f'ALTER TABLE datasets ADD COLUMN user_id INTEGER DEFAULT {admin_id}')
        
        # Drop the old unique constraint on name and create new one
        print("Updating table constraints...")
        
        # Create new table with proper schema
        cur.execute('''
            CREATE TABLE datasets_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                csv BLOB,
                user_id INTEGER NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, user_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Copy data from old table
        cur.execute('''
            INSERT INTO datasets_new (id, name, csv, user_id, uploaded_at)
            SELECT id, name, csv, user_id, uploaded_at FROM datasets
        ''')
        
        # Drop old table and rename new one
        cur.execute('DROP TABLE datasets')
        cur.execute('ALTER TABLE datasets_new RENAME TO datasets')
        
        # Create index
        cur.execute('CREATE INDEX idx_datasets_user_id ON datasets(user_id)')
        
        print("Successfully migrated datasets table")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Migration completed successfully!")
    print("\nDefault login credentials:")
    print("Username: admin")
    print("Password: admin123")
    print("\n⚠️  Please change the default password after first login!")

if __name__ == '__main__':
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nIf you have an existing database, you may need to back it up first.")