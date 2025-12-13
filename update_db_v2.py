
import sqlite3

DB_PATH = "imoveis.db"

def update_db_schema_v2():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("Checking users table columns...")
    cur.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in cur.fetchall()]
    
    if "whatsapp" not in cols:
        print("Adding whatsapp column to users...")
        cur.execute("ALTER TABLE users ADD COLUMN whatsapp TEXT")
    else:
        print("whatsapp column already exists.")
        
    if "is_temporary_password" not in cols:
        print("Adding is_temporary_password column to users...")
        cur.execute("ALTER TABLE users ADD COLUMN is_temporary_password INTEGER DEFAULT 0")
    else:
        print("is_temporary_password column already exists.")

    conn.commit()
    conn.close()
    print("Schema update v2 complete.")

if __name__ == "__main__":
    update_db_schema_v2()
