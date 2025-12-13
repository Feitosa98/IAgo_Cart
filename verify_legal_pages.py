
import urllib.request
import urllib.parse
import http.cookiejar

BASE_URL = "http://127.0.0.1:5000"

def verify_legal_pages():
    print("Verifying Legal Pages...")
    try:
        # Privacy
        resp = urllib.request.urlopen(f"{BASE_URL}/privacidade")
        if resp.getcode() == 200 and "Políticas de Privacidade" in resp.read().decode('utf-8'):
            print("[OK] Privacy Page Accessible")
        else:
            print("[FAIL] Privacy Page Error")

        # Terms
        resp = urllib.request.urlopen(f"{BASE_URL}/termos")
        if resp.getcode() == 200 and "Termos de Uso" in resp.read().decode('utf-8'):
            print("[OK] Terms Page Accessible")
        else:
            print("[FAIL] Terms Page Error")

    except Exception as e:
        print(f"[ERROR] Legal Pages Check: {e}")

if __name__ == "__main__":
    verify_legal_pages()
