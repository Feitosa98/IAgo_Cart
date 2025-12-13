import urllib.request
import sys

def check(url, content_signature):
    try:
        with urllib.request.urlopen(url) as response:
            html = response.read().decode('utf-8')
            if content_signature in html:
                print(f"[OK] {url}")
            else:
                print(f"[FAIL] {url} - Signature '{content_signature}' not found")
                # print(html[:500])
    except Exception as e:
        print(f"[ERROR] {url} - {e}")

print("Verifying endpoints...")
check("http://127.0.0.1:5000/", "navbar-toggler")
check("http://127.0.0.1:5000/importar", "Importar Matrícula")
check("http://127.0.0.1:5000/exportar/json", "INDICADOR_REAL")
