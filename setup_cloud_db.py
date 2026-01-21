
import psycopg2
import sys
from datetime import datetime

# Root connection to create DB
ROOT_URL = "postgresql://postgres:Manacapuru@indicador-onr-db.cr6ek2eqs8ci.sa-east-1.rds.amazonaws.com:5432/postgres"
TARGET_DB = "indicador_real"
TARGET_URL = f"postgresql://postgres:Manacapuru@indicador-onr-db.cr6ek2eqs8ci.sa-east-1.rds.amazonaws.com:5432/{TARGET_DB}"

def create_database():
    conn = psycopg2.connect(ROOT_URL)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{TARGET_DB}'")
    if not cur.fetchone():
        print(f"Creating database '{TARGET_DB}'...")
        cur.execute(f"CREATE DATABASE {TARGET_DB}")
    else:
        print(f"Database '{TARGET_DB}' already exists.")
    
    cur.close()
    conn.close()

def init_schemas():
    conn = psycopg2.connect(TARGET_URL)
    # Autocommit for some operations
    # conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
    cur = conn.cursor()
    
    # 1. Public Schema - Tenants
    print("Initializing Public Schema...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            schema_name TEXT UNIQUE NOT NULL,
            domain TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Iago Schema - Shared AI
    print("Initializing Iago Schema...")
    cur.execute("CREATE SCHEMA IF NOT EXISTS iago")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS iago.patterns (
            id SERIAL PRIMARY KEY,
            field_name TEXT NOT NULL,
            regex_pattern TEXT NOT NULL,
            example_match TEXT,
            weight INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)

    # 3. Default Tenant Schema
    tenant_slug = "default"
    schema_name = f"tenant_{tenant_slug}"
    print(f"Initializing Default Tenant ({schema_name})...")
    
    # Register Tenant
    cur.execute("INSERT INTO tenants (name, slug, schema_name) VALUES (%s, %s, %s) ON CONFLICT (slug) DO NOTHING", 
                ("Cartorio Default", tenant_slug, schema_name))
    
    # Create Schema
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
    
    # Apply Schema Tables (Imoveis, Users, etc.)
    # Note: We use search_path to simplify SQL
    cur.execute(f"SET search_path TO {schema_name}, public")
    
    # Users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            whatsapp TEXT,
            is_temporary_password INTEGER DEFAULT 0,
            profile_image TEXT,
            created_at TEXT,
            email TEXT,
            nome_completo TEXT,
            cpf TEXT,
            last_seen TEXT
        )
    """)
    
    # Imoveis
    cur.execute("""
        CREATE TABLE IF NOT EXISTS imoveis (
            id SERIAL PRIMARY KEY,
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
            
            updated_at TEXT,
            created_at TEXT
        )
    """)
    
    # Locks
    cur.execute("""
        CREATE TABLE IF NOT EXISTS imoveis_lock (
            imovel_id INTEGER PRIMARY KEY,
            editing_by TEXT,
            editing_since TEXT
        )
    """)

    # Config

    cur.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            id SERIAL PRIMARY KEY,
            username TEXT,
            name TEXT,
            status TEXT DEFAULT 'PENDENTE',
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print("Cloud DB Setup Complete.")

if __name__ == "__main__":
    create_database()
    init_schemas()
