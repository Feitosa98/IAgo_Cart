
import sqlite3
import psycopg2
import os
import json
from datetime import datetime

# Config
LOCAL_DB = "imoveis.db"
LOCAL_IA_DB = "ia.db"
CLOUD_URL = "postgresql://postgres:Manacapuru@indicador-onr-db.cr6ek2eqs8ci.sa-east-1.rds.amazonaws.com:5432/indicador_real"
TARGET_SCHEMA = "tenant_default"

def get_sqlite(db):
    if not os.path.exists(db):
        return None
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_users(pg_cur):
    print("Migrating Users...")
    conn = get_sqlite(LOCAL_DB)
    if not conn: return
    
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()
    
    pg_cur.execute(f"SET search_path TO {TARGET_SCHEMA}, public")
    
    for row in rows:
        r = dict(row)
        # Check specific columns mapping if needed, otherwise direct map
        pg_cur.execute(
            """
            INSERT INTO users (username, password_hash, role, whatsapp, is_temporary_password, profile_image, created_at, email, nome_completo, cpf, last_seen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
            """,
            (r['username'], r['password_hash'], r['role'], r.get('whatsapp'), r.get('is_temporary_password'), r.get('profile_image'), r.get('created_at'), r.get('email'), r.get('nome_completo'), r.get('cpf'), r.get('last_seen'))
        )
    conn.close()

def migrate_imoveis(pg_cur):
    print("Migrating Imoveis...")
    conn = get_sqlite(LOCAL_DB)
    if not conn: return
    
    cur = conn.cursor()
    cur.execute("SELECT * FROM imoveis")
    rows = cur.fetchall()
    
    pg_cur.execute(f"SET search_path TO {TARGET_SCHEMA}, public")
    
    for row in rows:
        r = dict(row)
        pg_cur.execute(
            """
            INSERT INTO imoveis (
                numero_registro, registro_tipo, status_trabalho, concluded_by, ocr_text, arquivo_tiff,
                nome_logradouro, numero_logradouro, complemento, bairro, cep, cidade, uf,
                tipo_de_imovel, localizacao, tipo_logradouro, varios_enderecos,
                loteamento, quadra, conjunto, setor, lote,
                contribuinte,
                rural_car, rural_nirf, rural_ccir, rural_numero_incra, rural_sigef, rural_denominacaorural, rural_acidentegeografico,
                condominio_nome, condominio_bloco, condominio_conjunto, condominio_torre, condominio_apto, condominio_vaga,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s
            )
            """,
            (
                r['numero_registro'], r['registro_tipo'], r['status_trabalho'], r.get('concluded_by'), r.get('ocr_text'), r.get('arquivo_tiff'),
                r.get('nome_logradouro'), r.get('numero_logradouro'), r.get('complemento'), r.get('bairro'), r.get('cep'), r.get('cidade'), r.get('uf'),
                r.get('tipo_de_imovel'), r.get('localizacao'), r.get('tipo_logradouro'), r.get('varios_enderecos'),
                r.get('loteamento'), r.get('quadra'), r.get('conjunto'), r.get('setor'), r.get('lote'),
                r.get('contribuinte'),
                r.get('rural_car'), r.get('rural_nirf'), r.get('rural_ccir'), r.get('rural_numero_incra'), r.get('rural_sigef'), r.get('rural_denominacaorural'), r.get('rural_acidentegeografico'),
                r.get('condominio_nome'), r.get('condominio_bloco'), r.get('condominio_conjunto'), r.get('condominio_torre'), r.get('condominio_apto'), r.get('condominio_vaga'),
                r.get('updated_at')
            )
        )
    conn.close()

def migrate_patterns(pg_cur):
    print("Migrating Patterns (IA)...")
    conn = get_sqlite(LOCAL_IA_DB)
    if not conn: return

    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM patterns")
        rows = cur.fetchall()
        
        pg_cur.execute("SET search_path TO iago, public")
        
        for row in rows:
            r = dict(row)
            pg_cur.execute(
                """
                INSERT INTO patterns (field_name, regex_pattern, example_match, weight, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (r['field_name'], r['regex_pattern'], r.get('example_match'), r.get('weight'), r.get('created_at'))
            )
    except:
        print("No patterns table or empty.")
    
    conn.close()

def run():
    pg_conn = psycopg2.connect(CLOUD_URL)
    pg_conn.autocommit = False
    pg_cur = pg_conn.cursor()
    
    try:
        migrate_users(pg_cur)
        migrate_imoveis(pg_cur)
        migrate_patterns(pg_cur)
        pg_conn.commit()
        print("Migration Success!")
    except Exception as e:
        pg_conn.rollback()
        print(f"Migration Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pg_conn.close()

if __name__ == "__main__":
    run()
