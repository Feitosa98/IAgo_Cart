
import psycopg2
import sys
import secrets
from werkzeug.security import generate_password_hash
from datetime import datetime

# Config
CLOUD_DB_URL = "postgresql://postgres:Manacapuru@indicador-onr-db.cr6ek2eqs8ci.sa-east-1.rds.amazonaws.com:5432/indicador_real"

def create_tenant(name, slug):
    conn = psycopg2.connect(CLOUD_DB_URL)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    schema_name = f"tenant_{slug}"
    print(f"Creating Tenant: {name} ({slug}) -> Schema: {schema_name}")

    try:
        # 1. Register in Public
        cur.execute("INSERT INTO tenants (name, slug, schema_name) VALUES (%s, %s, %s) RETURNING id", (name, slug, schema_name))
        print("Tenant registered.")
    except psycopg2.errors.UniqueViolation:
        print("Tenant slug already exists.")
        conn.close()
        return

    # 2. Create Schema
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
    print("Schema created.")

    # 3. Create Tables
    # We switch path to make it easier
    cur.execute(f"SET search_path TO {schema_name}, public")
    
    # Tables (Copy of setup_cloud_db logic)
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
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS imoveis (
            id SERIAL PRIMARY KEY,
            numero_registro TEXT,
            registro_tipo INTEGER,
            status_trabalho TEXT DEFAULT 'PENDENTE',
            concluded_by TEXT,
            ocr_text TEXT,
            arquivo_tiff TEXT,
            nome_logradouro TEXT, numero_logradouro TEXT, complemento TEXT, bairro TEXT, cep TEXT, cidade TEXT, uf INTEGER,
            tipo_de_imovel INTEGER, localizacao INTEGER, tipo_logradouro INTEGER, varios_enderecos TEXT,
            loteamento TEXT, quadra TEXT, conjunto TEXT, setor TEXT, lote TEXT,
            contribuinte TEXT,
            rural_car TEXT, rural_nirf TEXT, rural_ccir TEXT, rural_numero_incra TEXT, rural_sigef TEXT, rural_denominacaorural TEXT, rural_acidentegeografico TEXT,
            condominio_nome TEXT, condominio_bloco TEXT, condominio_conjunto TEXT, condominio_torre TEXT, condominio_apto TEXT, condominio_vaga TEXT,
            updated_at TEXT, created_at TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS imoveis_lock (
            imovel_id INTEGER PRIMARY KEY,
            editing_by TEXT,
            editing_since TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # 4. Create Admin User
    admin_pass = "admin123" # Default
    hashed = generate_password_hash(admin_pass)
    now = datetime.now().isoformat()
    cur.execute("INSERT INTO users (username, password_hash, role, created_at, nome_completo) VALUES (%s, %s, %s, %s, %s)", 
                ("admin", hashed, "admin", now, "Administrador"))
    
    print(f"Tenant Setup Complete. Admin User: admin / {admin_pass}")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_tenant.py <Name> <slug>")
        print("Example: python create_tenant.py 'Cartorio 1 Oficio' 'cartorio1'")
    else:
        create_tenant(sys.argv[1], sys.argv[2])
