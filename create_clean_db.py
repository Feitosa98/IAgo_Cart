import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

DB_PATH = "imoveis.db"

def create_clean_db():
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except:
            print(f"Warning: Could not remove existing {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            whatsapp TEXT,
            is_temporary_password INTEGER DEFAULT 0,
            profile_image TEXT,
            created_at TEXT,
            email TEXT
        )
    """)
    
    # 2. Imoveis
    cur.execute("""
        CREATE TABLE IF NOT EXISTS imoveis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_registro TEXT,
            registro_tipo INTEGER,
            status_trabalho TEXT DEFAULT 'PENDENTE',
            concluded_by TEXT,
            ocr_text TEXT,
            arquivo_tiff TEXT,
            
            nome_logradouro TEXT,
            numero_logradouro TEXT,
            complemento TEXT,
            bairro TEXT,
            cep TEXT,
            cidade TEXT,
            uf INTEGER,
            
            tipo_de_imovel INTEGER,
            localizacao INTEGER,
            tipo_logradouro INTEGER,
            varios_enderecos TEXT,
            
            loteamento TEXT,
            quadra TEXT,
            conjunto TEXT,
            setor TEXT,
            lote TEXT,
            
            contribuinte TEXT,
            
            rural_car TEXT,
            rural_nirf TEXT,
            rural_ccir TEXT,
            rural_numero_incra TEXT,
            rural_sigef TEXT,
            rural_denominacaorural TEXT,
            rural_acidentegeografico TEXT,
            
            condominio_nome TEXT,
            condominio_bloco TEXT,
            condominio_conjunto TEXT,
            condominio_torre TEXT,
            condominio_apto TEXT,
            condominio_vaga TEXT,
            
            updated_at TEXT
        )
    """)

    # 3. Locks
    cur.execute("""
        CREATE TABLE IF NOT EXISTS imoveis_lock (
            imovel_id INTEGER PRIMARY KEY,
            editing_by TEXT,
            editing_since TEXT
        )
    """)

    # 4. Resets
    cur.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            name TEXT,
            status TEXT DEFAULT 'PENDENTE',
            created_at TEXT
        )
    """)
    
    # 5. Config
    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # INSERT DEFAULT ADMIN
    hashed = generate_password_hash("admin") # Default password
    now = (datetime.utcnow() - timedelta(hours=4)).isoformat()
    cur.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)", 
                ("admin", hashed, "admin", now))
    
    # Insert Default Config
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
    print("Database created successfully.")

if __name__ == "__main__":
    create_clean_db()
