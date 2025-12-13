
import sqlite3

DB_PATH = "imoveis.db"

def update_db_v3():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("Checking users table columns...")
    cur.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in cur.fetchall()]
    
    if "profile_image" not in cols:
        print("Adding profile_image column to users...")
        cur.execute("ALTER TABLE users ADD COLUMN profile_image TEXT")
    else:
        print("profile_image column already exists.")
        
    conn.commit()
    conn.close()
    print("Schema update v3 complete.")

if __name__ == "__main__":
    update_db_v3()
