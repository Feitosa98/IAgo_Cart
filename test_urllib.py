import urllib.request
import ssl

print("-" * 20)
try:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    print("Testing HTTPS (192.168.0.221)...")
    with urllib.request.urlopen("https://192.168.0.221:5000", context=ctx, timeout=3) as r:
        print(f"HTTPS Status: {r.status}")
except Exception as e:
    print(f"HTTPS Fail: {e}")

print("-" * 20)
try:
    print("Testing HTTP (127.0.0.1)...")
    with urllib.request.urlopen("http://127.0.0.1:5000", timeout=3) as r:
        print(f"HTTP Status: {r.status}")
except Exception as e:
    print(f"HTTP Fail: {e}")
print("-" * 20)
