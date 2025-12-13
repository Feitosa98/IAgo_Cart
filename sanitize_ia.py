import sqlite3
try:
    conn = sqlite3.connect('ia.db')
    cur = conn.cursor()
    cur.execute("UPDATE patterns SET example_match = 'ANONYMIZED_DATA'")
    conn.commit()
    print("SUCCESS: AI Memory Sanitized")
except Exception as e:
    print(f"ERROR: {e}")
finally:
    if conn: conn.close()
