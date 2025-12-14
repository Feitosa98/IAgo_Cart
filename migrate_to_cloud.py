import sqlite3
import psycopg2
import os
from datetime import datetime

# Configuration
LOCAL_DB = "ia.db"
CLOUD_DB_URL = "postgresql://postgres:Manacapuru@indicador-onr-db.cr6ek2eqs8ci.sa-east-1.rds.amazonaws.com:5432"

def migrate():
    print("=== IAGO Migration Tool: Local -> Cloud ===")
    
    # 1. Check Local DB
    if not os.path.exists(LOCAL_DB):
        print(f"[ERROR] Local database '{LOCAL_DB}' not found. nothing to migrate.")
        return

    try:
        local_conn = sqlite3.connect(LOCAL_DB)
        local_conn.row_factory = sqlite3.Row
        local_cur = local_conn.cursor()
        
        # Check if table exists
        local_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patterns'")
        if not local_cur.fetchone():
            print("[INFO] 'patterns' table not found in local DB. New install? Nothing to migrate.")
            return

        local_cur.execute("SELECT field_name, regex_pattern, example_match, weight, created_at FROM patterns")
        rows = local_cur.fetchall()
        print(f"[INFO] Found {len(rows)} patterns in local database.")
        
    except Exception as e:
        print(f"[ERROR] Failed to read local DB: {e}")
        return

    if not rows:
        print("[INFO] No patterns to migrate.")
        return

    # 2. Connect to Cloud
    print("[INFO] Connecting to AWS Cloud Database...")
    try:
        cloud_conn = psycopg2.connect(CLOUD_DB_URL)
        cloud_cur = cloud_conn.cursor()
    except Exception as e:
        print(f"[ERROR] Connection to Cloud failed: {e}")
        return

    # 3. Create Table if not exists (in case cloud is empty)
    try:
        cloud_cur.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id SERIAL PRIMARY KEY,
                field_name TEXT NOT NULL,
                regex_pattern TEXT NOT NULL,
                example_match TEXT,
                weight INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)
        cloud_conn.commit()
    except Exception as e:
        print(f"[ERROR] Failed to init cloud schema: {e}")
        cloud_conn.rollback()
        return

    # 4. Migrate Data
    print("[INFO] Migrating patterns...")
    migrated = 0
    updated = 0
    
    for row in rows:
        field = row['field_name']
        regex = row['regex_pattern']
        example = row['example_match']
        weight = row['weight']
        created = row['created_at'] or datetime.now().isoformat()
        
        try:
            # Check existence
            cloud_cur.execute(
                "SELECT id, weight FROM patterns WHERE field_name=%s AND regex_pattern=%s",
                (field, regex)
            )
            existing = cloud_cur.fetchone()
            
            if existing:
                # Update weight (merge knowledge)
                new_weight = existing[1] + weight
                row_id = existing[0]
                cloud_cur.execute(
                    "UPDATE patterns SET weight = %s WHERE id = %s",
                    (new_weight, row_id)
                )
                updated += 1
            else:
                # Insert new
                cloud_cur.execute(
                    "INSERT INTO patterns (field_name, regex_pattern, example_match, weight, created_at) VALUES (%s, %s, %s, %s, %s)",
                    (field, regex, example, weight, created)
                )
                migrated += 1
                
        except Exception as e:
            print(f"[WARN] Failed to process pattern {field}: {e}")
            cloud_conn.rollback()
            continue

    cloud_conn.commit()
    cloud_conn.close()
    local_conn.close()
    
    print(f"=== Migration Complete ===")
    print(f"New Patterns: {migrated}")
    print(f"Updated Patterns: {updated}")
    print("Your AI brain is now in the cloud!")

if __name__ == "__main__":
    migrate()
