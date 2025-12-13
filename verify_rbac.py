
import urllib.request
import urllib.parse
import http.cookiejar

BASE_URL = "http://127.0.0.1:5000"

# Setup Cookie Jar for Session management
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

def test_public_access():
    print("Testing Public Access...")
    try:
        # Flask-Login redirects to /login?next=%2F
        resp = opener.open(f"{BASE_URL}/")
        content = resp.read().decode('utf-8')
        
        # Check if we landed on login page (either by URL or content)
        if "login" in resp.geturl() or "Acesse sua conta" in content:
            print("[OK] Index redirects to Login Page")
        else:
            print(f"[FAIL] Index did not redirect to login. URL: {resp.geturl()}")
            
    except Exception as e:
        print(f"[ERROR] Public Access: {e}")

def test_login():
    print("\nTesting Login...")
    try:
        login_data = urllib.parse.urlencode({
            "username": "admin", 
            "password": "admin"
        }).encode()
        
        # POST to /login
        resp = opener.open(f"{BASE_URL}/login", data=login_data)
        content = resp.read().decode('utf-8')
        
        if "Dashboard" in content:
            print("[OK] Login successful (Dashboard link found)")
        elif "Início" in content:
             print("[OK] Login successful (Returned to Index)")
        else:
             print(f"[FAIL] Login failed. URL: {resp.geturl()}")
             # print(content[:200])

        # Test Access to Dashboard (using same cookie jar)
        resp = opener.open(f"{BASE_URL}/dashboard")
        if resp.status == 200:
             print("[OK] Dashboard accessible")
        else:
             print(f"[FAIL] Dashboard Status: {resp.status}")

    except Exception as e:
        print(f"[ERROR] Login Test: {e}")

if __name__ == "__main__":
    test_public_access()
    test_login()
