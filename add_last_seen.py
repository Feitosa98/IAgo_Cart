import sqlite3

DB_PATH = "imoveis.db"

def migrate():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        print("Adding last_seen column to users table...")
        cur.execute("ALTER TABLE users ADD COLUMN last_seen DATETIME")
        print("Column added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column last_seen already exists.")
        else:
            print(f"Error: {e}")
    
    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()
