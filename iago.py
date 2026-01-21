
from dotenv import load_dotenv
import sqlite3
import re
import os
from datetime import datetime
import requests


# Load .env file
load_dotenv()

IAGO_SERVER_URL = os.getenv("IAGO_SERVER_URL")

import db_manager

# ...

def get_ia_conn():
    # Use Shared Cloud DB from db_manager
    conn = db_manager.get_compat_conn()
    
    # Set Schema to IAGO
    try:
        cur = conn.conn.cursor()
        cur.execute("SET search_path TO iago, public")
        cur.close()
        conn.commit()
    except Exception as e:
        print(f"[IAGO DB ERROR] Failed to set schema: {e}")
        
    return conn



def init_ia_db():
    conn = get_ia_conn()
    cur = conn.cursor()
    
    # Postgres Schema
    # We rely on setup_cloud_db.py generally, but this is safe to keep
    # Note: cur is wrapped, so ? is replaced.
    # But for DDL, ? is not used.
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS patterns (
            id SERIAL PRIMARY KEY,
            field_name TEXT NOT NULL,
            regex_pattern TEXT NOT NULL,
            example_match TEXT,
            weight INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


# ... (rest of imports/helpers)

def learn(full_text, current_data):
    if not full_text:
        return 0
        
    # --- API MODE (Client) ---
    if IAGO_SERVER_URL:
        # ... (Client code unchanged) ...
        try:
            payload = {"full_text": full_text, "current_data": current_data}
            resp = requests.post(f"{IAGO_SERVER_URL}/api/iago/learn", json=payload, timeout=5)
            if resp.status_code == 200:
                return resp.json().get('learned_count', 0)
            return 0
        except Exception as e:
            print(f"[IAGO CLIENT ERROR] Learn failed: {e}")
            return 0


    # --- SERVER/LOCAL MODE (DB Access) ---
    try:
        conn = get_ia_conn()
        cur = conn.cursor()
        count = 0
        now = datetime.now().isoformat()
        
        target_fields = [
            "NUMERO_REGISTRO", "NOME_LOGRADOURO", "BAIRRO", 
            "CIDADE", "LOTE", "QUADRA", "SETOR"
        ]
        
        for field in target_fields:
            val = current_data.get(field) or current_data.get(field.lower())
            
            if val:
                val_str = str(val).strip()
                regex = generate_context_regex(full_text, val_str)
                
                if regex:
                    # Check
                    cur.execute("SELECT id, weight FROM patterns WHERE field_name=? AND regex_pattern=?", (field, regex))
                    existing = cur.fetchone()

                    if existing:
                        # Reinforce
                        # Wrapper returns dict-like or tuple? Wrapper fetchone returns what cursor returns.
                        # DictCursor returns RealDictRow (dict-like).
                        # Tuple cursor returns tuple.
                        # Our db_manager uses DictCursor.
                        row_id = existing['id']
                        cur.execute("UPDATE patterns SET weight = weight + 1 WHERE id=?", (row_id,))
                    else:
                        # Learn
                        anonymized_example = f"Pattern for {field}" 
                        cur.execute("INSERT INTO patterns (field_name, regex_pattern, example_match, created_at) VALUES (?, ?, ?, ?)",
                                    (field, regex, anonymized_example, now))
                        count += 1
        
        conn.commit()
        conn.close()
        return count
    except Exception as e:
        print(f"[IAGO DB ERROR] Learn: {e}")
        return 0

def analyze(full_text):
    """
    Applies learned patterns to text.
    """
    if not full_text:
        return {}

    # --- API MODE ---
    if IAGO_SERVER_URL:
        try:
            payload = {"full_text": full_text}
            # We ask server to analyze
            resp = requests.post(f"{IAGO_SERVER_URL}/api/iago/analyze", json=payload, timeout=5)
            if resp.status_code == 200:
                return resp.json()
            return {}
        except Exception as e:
            print(f"[IAGO CLIENT ERROR] Analyze failed: {e}")
            return {}
        

    # --- SERVER/LOCAL MODE (DB Access) ---
    try:
        conn = get_ia_conn()
        cur = conn.cursor()
        
        # Explicitly use iago.patterns to avoid path issues
        cur.execute("SELECT field_name, regex_pattern FROM iago.patterns ORDER BY weight DESC")
        rows = cur.fetchall()
        conn.close()
        
        print(f"[IAGO] Analysis: Found {len(rows)} patterns.")
        
        results = {}
        
        for r in rows:
            # Handle row access difference
            field = r["field_name"]
            if field in results:
                continue
                
            pattern = r["regex_pattern"]
            try:
                match = re.search(pattern, full_text)
                if match:
                    val = match.group(1).strip()
                    results[field] = val
            except re.error:
                pass
                
        return results
    except Exception as e:
        print(f"[IAGO DB ERROR] Analyze: {e}")
        return {}

