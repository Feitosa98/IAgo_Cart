import psycopg2
import sys

# URL from migrate_to_cloud.py
CLOUD_DB_URL = "postgresql://postgres:Manacapuru@indicador-onr-db.cr6ek2eqs8ci.sa-east-1.rds.amazonaws.com:5432"

try:
    print(f"Connecting to {CLOUD_DB_URL}...")
    conn = psycopg2.connect(CLOUD_DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    ver = cur.fetchone()
    print(f"Connected! Version: {ver[0]}")
    
    # Check if we can create databases
    # Usually requires autocommit mode for CREATE DATABASE
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    
    # Check existing DBs
    cur.execute("SELECT datname FROM pg_database WHERE datname='onr_master';")
    exists = cur.fetchone()
    if exists:
        print("Database 'onr_master' already exists.")
    else:
        print("Database 'onr_master' does not exist (I can propose creating it).")

    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
