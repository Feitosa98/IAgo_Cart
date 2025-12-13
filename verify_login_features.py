
import urllib.request
import urllib.parse
import http.cookiejar

BASE_URL = "http://127.0.0.1:5000"

# Setup Cookie Jar
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

def verify_login_page_elements():
    print("Verifying Login Page Elements...")
    try:
        resp = opener.open(f"{BASE_URL}/login")
        content = resp.read().decode('utf-8')
        
        # Check Show Password feature (HTML/JS)
        if 'id="togglePassword"' in content:
            print("[OK] Show Password toggle found")
        else:
            print("[FAIL] Show Password toggle MISSING")
            
        # Check Recovery Link
        if 'recuperar_senha' in content:
             print("[OK] Recovery Password link found")
        else:
             print("[FAIL] Recovery Password link MISSING")

        # Check Footer
        if "Lucas Espirtusanto" in content and "Feitosa Soluções" in content:
             print("[OK] Footer credits found")
        else:
             print("[FAIL] Footer credits MISSING")
             
    except Exception as e:
        print(f"[ERROR] Login Page Check: {e}")

def verify_recovery_submission():
    print("\nVerifying Recovery Submission...")
    try:
        data = urllib.parse.urlencode({
            "username": "lost_user",
            "name": "Lost User Name"
        }).encode()
        
        resp = opener.open(f"{BASE_URL}/recuperar_senha", data=data)
        # Should redirect to login with flash message
        content = resp.read().decode('utf-8')
        
        if "Solicitação enviada" in content or "Login" in content or "/login" in resp.geturl(): 
             # Check if we are back at login page
             print("[OK] Recovery submission redirected correctly")
        else:
             print(f"[FAIL] Recovery submission unexpected response. URL: {resp.geturl()}")

    except Exception as e:
         print(f"[ERROR] Recovery Check: {e}")

if __name__ == "__main__":
    verify_login_page_elements()
    verify_recovery_submission()
