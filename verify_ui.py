import urllib.request
import sys

def check(url, content_signature):
    try:
        with urllib.request.urlopen(url) as response:
            html = response.read().decode('utf-8')
            if content_signature in html:
                print(f"[OK] {url} - Found '{content_signature}'")
            else:
                print(f"[FAIL] {url} - Signature '{content_signature}' not found")
    except Exception as e:
        print(f"[ERROR] {url} - {e}")

def check_status(url):
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                 print(f"[OK] {url} - Status 200")
            else:
                 print(f"[FAIL] {url} - Status {response.status}")
    except Exception as e:
        print(f"[ERROR] {url} - {e}")

print("Verifying UI updates...")
check("http://127.0.0.1:5000/", "sidebar")
check("http://127.0.0.1:5000/", "logo.png")
check("http://127.0.0.1:5000/", "Usuário Web")
check_status("http://127.0.0.1:5000/static/logo.png")
