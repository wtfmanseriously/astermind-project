import sqlite3

DB_PATH = 'astermind.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        value REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        FOREIGN KEY (entity_id) REFERENCES entities (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        evidence TEXT,
        reasoning TEXT,
        verdict TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (entity_id) REFERENCES entities (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        previous_hash TEXT NOT NULL,
        hash TEXT NOT NULL
    )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM audit_logs')
    if cursor.fetchone()[0] == 0:
        import hashlib
        initial_hash = hashlib.sha256(b"genesis").hexdigest()
        cursor.execute('INSERT INTO audit_logs (action, previous_hash, hash) VALUES (?, ?, ?)', 
                      ('System Initialized', '0', initial_hash))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
