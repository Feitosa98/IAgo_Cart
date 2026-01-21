
import requests
import re
import sys

URL = "http://localhost:5005/login"

s = requests.Session()

print("1. GET /login...")
try:
    r = s.get(URL)
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print("Failed to load login page")
        sys.exit(1)
        
    # Extract CSRF
    match = re.search(r'name="csrf_token" value="([^"]+)"', r.text)
    if not match:
        print("No CSRF token found in HTML!")
        print(r.text[:500])
        sys.exit(1)
        
    token = match.group(1)
    print(f"Token found: {token}")
    print(f"Cookies: {s.cookies.get_dict()}")
    
    # 2. POST
    print("2. POST /login...")
    payload = {
        "username": "admin",
        "password": "wrongpassword", # Just to check CSRF pass
        "cartorio": "default",
        "csrf_token": token
    }
    
    r = s.post(URL, data=payload)
    print(f"Status: {r.status_code}")
    if r.status_code == 403 and "CSRF Token missing or invalid" in r.text:
        print(" reproduced CSRF Error!")
    elif r.status_code == 200 and "Usuário," in r.text: # Flash message
        print("CSRF Passed (Invalid credentials as expected)")
    else:
        print(f"Unexpected result: {r.text[:200]}")

except Exception as e:
    print(f"Error: {e}")
