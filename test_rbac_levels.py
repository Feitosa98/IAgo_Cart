
import sqlite3
import urllib.request
import urllib.parse
import http.cookiejar
from werkzeug.security import generate_password_hash
from datetime import datetime

DB_PATH = "imoveis.db"
BASE_URL = "http://127.0.0.1:5000"

def seed_users():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    users = [
        ("supervisor", "123", "supervisor"),
        ("colaborador", "123", "colaborador")
    ]
    
    print("--- Seeding/Checking Users ---")
    for username, pwd, role in users:
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
        if not cur.fetchone():
            print(f"Creating user: {username} ({role})")
            hashed = generate_password_hash(pwd)
            cur.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                        (username, hashed, role, datetime.now().isoformat()))
        else:
            print(f"User {username} already exists.")
            
    conn.commit()
    conn.close()

def test_login(username, password, role_name):
    print(f"\nTesting Login for: {role_name.upper()} ({username})")
    
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    # 1. Login
    try:
        data = urllib.parse.urlencode({"username": username, "password": password}).encode()
        resp = opener.open(f"{BASE_URL}/login", data=data)
        content = resp.read().decode('utf-8')
        
        # Check if login succeeded (Check for logout link or specific content)
        if "/logout" in content or "Sair" in content:
             print("[OK] Login Successful")
        else:
             print(f"[FAIL] Login Failed for {username}")
             return

        # 2. Test Dashboard Access
        print(" -> Attempting Dashboard Access...")
        resp = opener.open(f"{BASE_URL}/dashboard")
        content = resp.read().decode('utf-8')
        
        if role_name == "colaborador":
            # Expect redirect to Index (Flash message "Acesso negado" might be present if parsed, but URL check is easier)
            if "Dashboard" in content and "Total Matrículas" in content:
                 print("[FAIL] Colaborador was able to access Dashboard!")
            elif "Matrículas" in content or "Início" in content:
                 print("[OK] Colaborador redirected to Index (Access Denied to Dashboard)")
            else:
                 print(f"[?] Unexpected content for Colaborador: {resp.geturl()}")
                 
        else: # Admin / Supervisor
            if "Total Matrículas" in content:
                print("[OK] Dashboard Accessible")
            else:
                print("[FAIL] Dashboard NOT Accessible (Unexpected)")

        # 3. Logout
        opener.open(f"{BASE_URL}/logout")
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    seed_users()
    test_login("admin", "admin", "admin")
    test_login("supervisor", "123", "supervisor")
    test_login("colaborador", "123", "colaborador")
