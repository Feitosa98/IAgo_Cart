import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    print("Testando HTTP (plain)...")
    try:
        r = requests.get("http://127.0.0.1:5000", timeout=2)
        print(f"HTTP Status: {r.status_code}")
    except Exception as e:
        print(f"HTTP Falhou: {e}")

    print("\nTestando HTTPS (SSL)...")
    try:
        r = requests.get("https://127.0.0.1:5000", verify=False, timeout=2)
        print(f"HTTPS Status: {r.status_code}")
    except Exception as e:
        print(f"HTTPS Falhou: {e}")

except Exception as e:
    print(f"Erro Geral: {e}")
