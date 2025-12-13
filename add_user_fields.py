import sqlite3

def add_columns():
    conn = sqlite3.connect("imoveis.db")
    cur = conn.cursor()
    
    try:
        cur.execute("ALTER TABLE users ADD COLUMN nome_completo TEXT")
        print("Coluna 'nome_completo' adicionada.")
    except sqlite3.OperationalError as e:
        print(f"Erro ao adicionar 'nome_completo': {e}")
        
    try:
        cur.execute("ALTER TABLE users ADD COLUMN cpf TEXT")
        print("Coluna 'cpf' adicionada.")
    except sqlite3.OperationalError as e:
        print(f"Erro ao adicionar 'cpf': {e}")

    # Unique constraint cannot be added easily via ALTER TABLE in SQLite (except via index)
    try:
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_cpf ON users(cpf) WHERE cpf IS NOT NULL AND cpf != ''")
        print("Índice UNIQUE para CPF criado.")
    except Exception as e:
        print(f"Erro ao criar índice UNIQUE para CPF: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_columns()
