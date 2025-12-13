
import sqlite3

DB_PATH = "imoveis.db"

def update_db_resets():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Create password_resets Table
    print("Creating password_resets table...")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        name TEXT NOT NULL,
        status TEXT DEFAULT 'PENDENTE',
        created_at TEXT
    )
    """)
    
    conn.commit()
    conn.close()
    print("Database update for resets complete.")

if __name__ == "__main__":
    update_db_resets()
