
import sys
import os

# Filter Tesseract/Poppler warnings
os.environ["TESSERACT_CMD"] = "echo" 

try:
    print("Importing app...")
    import imoveis_web
    print("App imported.")
    
    app = imoveis_web.app
    print("App initialized.")

    with app.app_context():
        # Test Connection using our new logic
        # Mock session if needed? No, user logic handles missing session by using default.
        print("Testing DB connection...")
        conn = imoveis_web.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        print(f"DB Check: {cur.fetchone()}")
        conn.close()
        
    print("Verification Success!")
except Exception as e:
    print(f"Verification Failed: {e}")
    import traceback
    traceback.print_exc()
