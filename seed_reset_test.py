
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

DB_PATH = "imoveis.db"

def seed_test_data():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 1. Ensure Admin exists
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        hashed = generate_password_hash("admin")
        now = (datetime.utcnow() - timedelta(hours=4)).isoformat()
        cur.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                ("admin", hashed, "admin", now))
                    
    # 2. Create/Update Test User
    username = "usuario_teste"
    whatsapp = "5511999998888"
    cur.execute("DELETE FROM users WHERE username=?", (username,))
    
    hashed = generate_password_hash("oldpass")
    now = (datetime.utcnow() - timedelta(hours=4)).isoformat()
    cur.execute("INSERT INTO users (username, password_hash, role, whatsapp, created_at) VALUES (?, ?, ?, ?, ?)",
                (username, hashed, "colaborador", whatsapp, now))
    
    # 3. Create Reset Request
    # Clear old requests for clean slate
    cur.execute("DELETE FROM password_resets")
    
    cur.execute("INSERT INTO password_resets (username, name, status, created_at) VALUES (?, ?, 'PENDENTE', ?)",
                (username, "Teste Testador", now))
                
    conn.commit()
    conn.close()
    print("Test data seeded: Admin (admin/admin), User (usuario_teste), Reset Request (PENDENTE).")

if __name__ == "__main__":
    seed_test_data()
