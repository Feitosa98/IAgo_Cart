
import sqlite3

def add_created_at():
    DB_PATH = "imoveis.db"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        # Check if column exists
        cur.execute("PRAGMA table_info(imoveis)")
        columns = [row[1] for row in cur.fetchall()]
        
        if "created_at" not in columns:
            print("Adding created_at column...")
            cur.execute("ALTER TABLE imoveis ADD COLUMN created_at TEXT")
            conn.commit()
            print("Column added.")
        else:
            print("Column created_at already exists.")
            
    except Exception as e:
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    add_created_at()
