import time
import db_manager
import statistics

def test_latency():
    print("Initializing Pool...")
    t0 = time.time()
    db_manager.init_pool()
    print(f"Pool Init: {time.time()-t0:.4f}s")
    
    latencies = []
    print("\nTesting 10 simple queries...")
    
    conn = db_manager.get_compat_conn()
    cur = conn.cursor()
    
    for i in range(10):
        start = time.time()
        cur.execute("SELECT 1")
        cur.fetchone()
        duration = time.time() - start
        latencies.append(duration)
        print(f"Query {i+1}: {duration:.4f}s")
    
    conn.close()
    
    avg = statistics.mean(latencies)
    max_lat = max(latencies)
    min_lat = min(latencies)
    
    print(f"\nResults:")
    print(f"Average: {avg:.4f}s")
    print(f"Min: {min_lat:.4f}s")
    print(f"Max: {max_lat:.4f}s")
    
    if avg > 0.1:
        print("\nWARNING: High latency detected (>100ms per simple query).")
    else:
        print("\nLatency looks acceptable for cloud DB.")

if __name__ == "__main__":
    test_latency()
