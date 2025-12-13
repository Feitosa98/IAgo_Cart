import sqlite3

DB_PATH = "imoveis.db"

def update_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        # Add concluded_by column
        try:
            cur.execute("ALTER TABLE imoveis ADD COLUMN concluded_by TEXT")
            print("Coluna 'concluded_by' adicionada com sucesso.")
        except sqlite3.OperationalError:
            print("Coluna 'concluded_by' já existe.")
            
        conn.commit()
    except Exception as e:
        print(f"Erro ao atualizar banco: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_db()
