import db_manager

try:
    conn = db_manager.get_compat_conn()
    cur = conn.cursor()
    
    # Check Imoveis Columns
    try:
        cur.execute("SELECT * FROM imoveis LIMIT 0")
        print("Imoveis Columns:", [d[0] for d in cur.description])
    except Exception as e:
        print("Error checking imoveis:", e)

    # Check Audit Logs
    try:
        cur.execute("SELECT * FROM information_schema.tables WHERE table_name='audit_logs'")
        if cur.fetchone():
            print("Table 'audit_logs' EXISTS.")
            cur.execute("SELECT * FROM audit_logs LIMIT 0")
            print("Audit Logs Columns:", [d[0] for d in cur.description])
        else:
            print("Table 'audit_logs' DOES NOT EXIST.")
    except Exception as e:
        print("Error checking audit_logs:", e)
        
    conn.close()
except Exception as e:
    print("DB Connection Error:", e)
