
import sqlite3

def check_schema():
    conn = sqlite3.connect("imoveis.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("Table Info for 'users':")
    cur.execute("PRAGMA table_info(users)")
    for col in cur.fetchall():
        print(dict(col))

    print("\nTable Info for 'password_resets':")
    cur.execute("PRAGMA table_info(password_resets)")
    rows = cur.fetchall()
    if not rows:
        print("Table 'password_resets' DOES NOT EXIST.")
    else:
        for col in rows:
            print(dict(col))
        
    print("\nSample Data:")
    cur.execute("SELECT * FROM users LIMIT 1")
    row = cur.fetchone()
    if row:
        print(dict(row))
        print("Keys:", row.keys())
    else:
        print("No users found.")

    conn.close()

if __name__ == "__main__":
    check_schema()
