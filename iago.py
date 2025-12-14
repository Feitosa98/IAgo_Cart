
from dotenv import load_dotenv
import sqlite3
import re
import os
from datetime import datetime

# Load .env file
load_dotenv()



try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None

# DB Configuration
IAGO_DB_TYPE = os.getenv("IAGO_DB_TYPE", "sqlite") # 'sqlite' or 'postgres'
IAGO_DB_URL = os.getenv("IAGO_DB_URL", "") # e.g. "postgresql://user:pass@host/db"
IA_DB_PATH = os.getenv("IAGO_DB_PATH", "ia.db")

print(f"[IAGO] DB Type: {IAGO_DB_TYPE}")
if IAGO_DB_TYPE == 'sqlite':
    print(f"[IAGO] Path: {os.path.abspath(IA_DB_PATH)}")

def get_ia_conn():
    if IAGO_DB_TYPE == 'postgres':
        if not psycopg2:
            raise ImportError("psycopg2 is required for Postgres usage. pip install psycopg2-binary")
        return psycopg2.connect(IAGO_DB_URL)
        
    # Default SQLite
    db_dir = os.path.dirname(IA_DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(IA_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(cur, sql, params=()):
    """Helper to handle placeholder differences (sqlite: ?, postgres: %s)"""
    if IAGO_DB_TYPE == 'postgres':
        # Convert ? to %s for postgres
        sql = sql.replace('?', '%s')
    cur.execute(sql, params)

def init_ia_db():
    conn = get_ia_conn()
    cur = conn.cursor()
    
    # Schema adaption
    pk_def = "INTEGER PRIMARY KEY AUTOINCREMENT"
    if IAGO_DB_TYPE == 'postgres':
        pk_def = "SERIAL PRIMARY KEY"
        
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS patterns (
            id {pk_def},
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
                    execute_query(cur, "SELECT id, weight FROM patterns WHERE field_name=? AND regex_pattern=?", (field, regex))
                    existing = None
                    if IAGO_DB_TYPE == 'postgres':
                        # Postgres cursor might behave differently depending on factory
                        # but standard psycopg2 cursor fetches tuples or RealDictRow
                        existing = cur.fetchone()
                    else:
                         existing = cur.fetchone()

                    if existing:
                        # Reinforce
                        # Handle row access difference if simple tuple
                        row_id = existing['id'] if hasattr(existing, 'keys') else existing[0]
                        execute_query(cur, "UPDATE patterns SET weight = weight + 1 WHERE id=?", (row_id,))
                    else:
                        # Learn
                        anonymized_example = f"Pattern for {field}" 
                        execute_query(cur, "INSERT INTO patterns (field_name, regex_pattern, example_match, created_at) VALUES (?, ?, ?, ?)",
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
        execute_query(cur, "SELECT field_name, regex_pattern FROM patterns ORDER BY weight DESC")
        rows = cur.fetchall()
        conn.close()
        
        results = {}
        
        for r in rows:
            # Handle row access difference
            field = r["field_name"] if hasattr(r, 'keys') else r[0]
            if field in results:
                continue
                
            pattern = r["regex_pattern"] if hasattr(r, 'keys') else r[1]
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
