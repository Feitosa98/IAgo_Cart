
import psycopg2
import sys
from datetime import datetime

# Config (Should ideally load from env or db_manager, but hardcoded for script reliability)
CLOUD_DB_URL = "postgresql://postgres:Manacapuru@indicador-onr-db.cr6ek2eqs8ci.sa-east-1.rds.amazonaws.com:5432/indicador_real"

def migrate_auth_to_global():
    conn = psycopg2.connect(CLOUD_DB_URL)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    print("--- Starting Global Auth Migration ---")

    # 1. Create public.users
    # We mirror the schema of the tenant users, but this one is authoritative for Auth.
    print("1. Creating public.users table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            email TEXT,
            nome_completo TEXT,
            cpf TEXT,
            whatsapp TEXT,
            profile_image TEXT,
            is_temporary_password INTEGER DEFAULT 0,
            last_seen TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    

    # 2. Create public.user_tenants
    print("2. Creating public.user_tenants table...")
    cur.execute("DROP TABLE IF EXISTS public.user_tenants")
    cur.execute("""
        CREATE TABLE public.user_tenants (
            user_id INTEGER REFERENCES public.users(id) ON DELETE CASCADE,
            tenant_id INTEGER REFERENCES public.tenants(id) ON DELETE CASCADE,
            role_in_tenant TEXT DEFAULT 'user',
            PRIMARY KEY (user_id, tenant_id)
        )
    """)

    # 3. Migrate Users from tenant_default (assuming it's the primary source of truth for now)
    print("3. Migrating users from tenant_default...")
    
    # Get Tenant ID for default
    cur.execute("SELECT id, schema_name FROM tenants WHERE slug='default' OR schema_name='tenant_default'")
    default_tenant = cur.fetchone()
    
    if not default_tenant:
        # Create default tenant entry if missing
        print("   - Default tenant not found in public.tenants, creating...")
        cur.execute("INSERT INTO tenants (name, slug, schema_name) VALUES ('Cartório Padrão', 'default', 'tenant_default') RETURNING id")
        default_tenant_id = cur.fetchone()[0]
    else:
        default_tenant_id = default_tenant[0]

    # Fetch existing users from tenant_default
    try:
        cur.execute(f"SELECT username, password_hash, role, email, nome_completo, cpf, whatsapp, is_temporary_password, created_at FROM tenant_default.users")
        rows = cur.fetchall()
        
        for r in rows:
            username = r[0]
            # Insert into public.users
            cur.execute("""
                INSERT INTO public.users (username, password_hash, role, email, nome_completo, cpf, whatsapp, is_temporary_password, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE SET last_seen=EXCLUDED.last_seen -- Just a dummy update to get ID
                RETURNING id
            """, r)
            user_id = cur.fetchone()[0]
            
            # Link to tenant
            cur.execute("""
                INSERT INTO public.user_tenants (user_id, tenant_id, role_in_tenant)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (user_id, default_tenant_id, r[2]))
            
            print(f"   - Migrated {username} -> Global ID {user_id}")
            
    except Exception as e:
        print(f"   ! Error reading tenant_default users (maybe table empty or missing?): {e}")

    # 4. Ensure Admin exists
    # If no admin, create one
    cur.execute("SELECT 1 FROM public.users WHERE username='admin'")
    if not cur.fetchone():
        print("4. Creating Default Admin...")
        from werkzeug.security import generate_password_hash
        hashed = generate_password_hash("admin123")
        now = datetime.now().isoformat()
        
        cur.execute("INSERT INTO public.users (username, password_hash, role, created_at, nome_completo) VALUES (%s, %s, 'admin', %s, 'Super Admin') RETURNING id", 
                    ("admin", hashed, now))
        uid = cur.fetchone()[0]
        
        # Admin has access to ALL tenants? Or just default?
        # Let's give access to default for now
        cur.execute("INSERT INTO public.user_tenants (user_id, tenant_id, role_in_tenant) VALUES (%s, %s, 'admin')", (uid, default_tenant_id))

    print("--- Migration Complete ---")
    conn.close()

if __name__ == "__main__":
    migrate_auth_to_global()
