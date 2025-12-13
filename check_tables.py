
import sqlite3
import os

files = ["imoveis.db", "imoveis - Copia.db"]

for f in files:
    if not os.path.exists(f):
        print(f"File {f} not found.")
        continue
        
    print(f"--- Tables in {f} ---")
    try:
        conn = sqlite3.connect(f)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        print(tables)
        conn.close()
    except Exception as e:
        print(f"Error reading {f}: {e}")
    print("\n")
