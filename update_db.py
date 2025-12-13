
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

DB_PATH = "imoveis.db"

def update_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 1. Create Users Table
    print("Creating users table...")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT
    )
    """)
    
    # 2. Add status_trabalho to imoveis
    print("Checking imoveis table columns...")
    cur.execute("PRAGMA table_info(imoveis)")
    cols = [r[1] for r in cur.fetchall()]
    
    if "status_trabalho" not in cols:
        print("Adding status_trabalho column...")
        cur.execute("ALTER TABLE imoveis ADD COLUMN status_trabalho TEXT DEFAULT 'PENDENTE'")
    else:
        print("status_trabalho already exists.")

    # 3. Seed Default Admin
    print("Seeding default admin...")
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        hashed = generate_password_hash("admin")
        now = datetime.utcnow().isoformat()
        cur.execute("INSERT INTO users (username, password, role, created_at) VALUES (?, ?, ?, ?)",
                    ("admin", hashed, "admin", now))
        print("Default admin created.")
    else:
        print("Admin user already exists.")

    conn.commit()
    conn.close()
    print("Database update complete.")

if __name__ == "__main__":
    update_db()
