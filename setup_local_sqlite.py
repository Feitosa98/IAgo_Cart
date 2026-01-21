import sqlite3
import psycopg2
import os
from psycopg2.extras import RealDictCursor
from imoveis_web import User # Import User model idea if needed, or just raw sql

# CONFIG
CLOUD_DB_URL = "postgresql://postgres:Manacapuru@indicador-onr-db.cr6ek2eqs8ci.sa-east-1.rds.amazonaws.com:5432/indicador_real"

def get_cloud_conn():
    return psycopg2.connect(CLOUD_DB_URL, cursor_factory=RealDictCursor)

def setup_local_public():
    print("Setting up local_public.db...")
    if os.path.exists("local_public.db"):
        os.remove("local_public.db")
        
    l_conn = sqlite3.connect("local_public.db")
    l_cur = l_conn.cursor()
    
    # Cloud Data
    c_conn = get_cloud_conn()
    c_cur = c_conn.cursor()
    
    # 1. Tenants
    print("Syncing Tenants...")
    l_cur.execute("""
        CREATE TABLE tenants (
            id INTEGER PRIMARY KEY,
            name TEXT,
            slug TEXT UNIQUE,
            schema_name TEXT UNIQUE,
            domain TEXT,
            created_at TEXT
        )
    """)
    c_cur.execute("SELECT * FROM public.tenants")
    rows = c_cur.fetchall()
    for r in rows:
        l_cur.execute("INSERT INTO tenants (id, name, slug, schema_name, domain, created_at) VALUES (?,?,?,?,?,?)",
                      (r['id'], r['name'], r['slug'], r['schema_name'], r['domain'], str(r['created_at'])))
                      
    # 2. Users used to be global, but setup_cloud_db says they are per tenant?
    # Checking imoveis_web.py: User.get_by_username queries PUBLIC.users.
    # So we sync public.users.
    print("Syncing Users...")
    l_cur.execute("""
        CREATE TABLE users (
             id INTEGER PRIMARY KEY,
             username TEXT UNIQUE,
             password_hash TEXT,
             role TEXT,
             whatsapp TEXT,
             is_temporary_password INTEGER,
             profile_image TEXT,
             created_at TEXT,
             email TEXT,
             nome_completo TEXT,
             cpf TEXT,
             last_seen TEXT
        )
    """)
    
    # Check if public.users exists or if it's tenant specific.
    # Assuming code queries public.users.
    try:
        c_cur.execute("SELECT * FROM public.users")
        rows = c_cur.fetchall()
        for r in rows:
            l_cur.execute("""
                INSERT INTO users (id, username, password_hash, role, whatsapp, is_temporary_password, profile_image, created_at, email, nome_completo, cpf, last_seen)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (r['id'], r['username'], r['password_hash'], r['role'], r['whatsapp'], r['is_temporary_password'], r['profile_image'], str(r['created_at']), r['email'], r['nome_completo'], r['cpf'], str(r['last_seen'])))
    except Exception as e:
        print(f"Error syncing users: {e}")

    # 3. User Tenants (Many-to-Many)
    # Does it exist? imoveis_web.py line 873: JOIN user_tenants ut
    print("Syncing User Tenants...")
    l_cur.execute("CREATE TABLE user_tenants (user_id INTEGER, tenant_id INTEGER)")
    try:
        c_cur.execute("SELECT * FROM public.user_tenants")
        rows = c_cur.fetchall()
        for r in rows:
            l_cur.execute("INSERT INTO user_tenants (user_id, tenant_id) VALUES (?,?)", (r['user_id'], r['tenant_id']))
    except:
        print("user_tenants table might not exist in cloud public yet or named differently.")

    l_conn.commit()
    l_conn.close()
    c_conn.close()
    print("local_public.db Ready.")

def setup_local_tenant(slug, schema_name):
    db_name = f"local_{slug}.db"
    print(f"Setting up {db_name} ({schema_name})...")
    
    if os.path.exists(db_name):
        os.remove(db_name)
    
    l_conn = sqlite3.connect(db_name)
    l_cur = l_conn.cursor()
    
    c_conn = get_cloud_conn()
    c_cur = c_conn.cursor()
    
    # Set path
    c_cur.execute(f"SET search_path TO {schema_name}, public")
    
    # 1. Imoveis
    print("Syncing Imoveis...")
    # Schema matching setup_cloud_db.py but SQLite types
    l_cur.execute("""
        CREATE TABLE imoveis (
            id INTEGER PRIMARY KEY,
            numero_registro TEXT,
            registro_tipo INTEGER,
            status_trabalho TEXT,
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
    
    c_cur.execute("SELECT * FROM imoveis")
    rows = c_cur.fetchall()
    # We need to map dict rows to tuple for sqlite INSERT
    # Get columns from local table to match order?
    # Or just use named placeholders? SQLite supports :name.
    
    cols = [col[0] for col in c_cur.description]
    # Filter cols that exist in our create definition
    # For simplicity, we assume strict match or just insert what we defined.
    
    for r in rows:
        # Construct INSERT dict
        # Handle Timestamps
        r_clean = {k: str(v) if v is not None else None for k,v in r.items()}
        
        # Build query
        placeholders = ', '.join(['?'] * len(cols))
        columns = ', '.join(cols)
        vals = [r_clean[c] for c in cols]
        
        sql = f"INSERT INTO imoveis ({columns}) VALUES ({placeholders})"
        try:
            l_cur.execute(sql, vals)
        except Exception as e:
            # Maybe column mismatch
            print(f"Skipping row {r.get('id')}: {e}")

    l_conn.commit()
    l_conn.close()
    c_conn.close()
    print(f"{db_name} Ready.")

if __name__ == "__main__":
    setup_local_public()
    
    # Fetch tenants to sync
    l_conn = sqlite3.connect("local_public.db")
    l_cur = l_conn.cursor()
    l_cur.execute("SELECT slug, schema_name FROM tenants")
    tenants = l_cur.fetchall()
    l_conn.close()
    
    for slug, schema in tenants:
        setup_local_tenant(slug, schema)
