import sqlite3

DB_PATH = "imoveis.db"

def update_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Add email column to users table if it doesn't exist
    try:
        cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
        print("Column 'email' added to 'users' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'email' already exists in 'users' table.")
        else:
            print(f"Error adding column email: {e}")

    # 2. Create system_config table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    print("Table 'system_config' created/verified.")

    # Initialize default SMTP settings if empty
    defaults = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": "587",
        "smtp_user": "",
        "smtp_password": "",
        "smtp_tls": "1"
    }

    for key, val in defaults.items():
        cur.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES (?, ?)", (key, val))

    conn.commit()
    conn.close()
    print("Database updated successfully.")

if __name__ == "__main__":
    update_db()
