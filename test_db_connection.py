
import os
import sys
from dotenv import load_dotenv

# Load env variables forcefully
load_dotenv()

db_type = os.getenv("IAGO_DB_TYPE")
db_url = os.getenv("IAGO_DB_URL")

print(f"Testing Connection to: {db_type}")
print(f"URL: {db_url}")

if db_type != 'postgres':
    print("ERROR: IAGO_DB_TYPE is not postgres")
    sys.exit(1)

try:
    import psycopg2
    conn = psycopg2.connect(db_url)
    print("SUCCESS: Connection established!")
    
    # Test a simple query
    cur = conn.cursor()
    cur.execute("SELECT version();")
    ver = cur.fetchone()
    print(f"Database Version: {ver[0]}")
    
    conn.close()
    print("Connection closed.")
except Exception as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
