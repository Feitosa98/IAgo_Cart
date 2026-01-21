
import psycopg2
from psycopg2 import pool
import os
from flask import g
from contextlib import contextmanager

# Use the URL we verified
CLOUD_DB_URL = os.getenv("IAGO_DB_URL")
if not CLOUD_DB_URL:
    # Fallback only for local dev if needed, or raise error. 
    # Better to force env var for security.
    print("[WARNING] IAGO_DB_URL not found in env. DB connection may fail.")
# Note: The database name in URL is 'indicador_real'. We need to create it first if it doesn't exist.
# But for the pool, we assume it exists.

# Simple Pool
_pool = None

def init_pool():
    global _pool
    if _pool is None:
        try:
            _pool = psycopg2.pool.SimpleConnectionPool(1, 20, CLOUD_DB_URL)
            print("[DB] Connection Pool Initialized")
        except Exception as e:
            print(f"[DB] Pool Creation Failed: {e}")

def get_db_connection():
    global _pool
    if _pool is None:
        init_pool()
    return _pool.getconn()

def release_db_connection(conn):
    global _pool
    if _pool:
        _pool.putconn(conn)

class SQLiteCompatibleCursor:
    def __init__(self, cursor):
        self.cursor = cursor
        self.row_factory = None # Compat
        self._lastrowid = None

    def execute(self, sql, params=()):
        # Convert ? to %s
        sql = sql.replace('?', '%s')
        
        # Check if INSERT without RETURNING
        is_insert = sql.strip().upper().startswith("INSERT")
        if is_insert and "RETURNING" not in sql.upper():
            sql += " RETURNING id"
            self.cursor.execute(sql, params)
            try:
                self._lastrowid = self.cursor.fetchone()[0]
            except:
                self._lastrowid = None
            return self.cursor
            
        self._lastrowid = None
        return self.cursor.execute(sql, params)

    def executemany(self, sql, params_list):
        sql = sql.replace('?', '%s')
        return self.cursor.executemany(sql, params_list)
    
    def fetchone(self):
        return self.cursor.fetchone()
        
    def fetchall(self):
        return self.cursor.fetchall()
        
    def close(self):
        self.cursor.close()
        
    @property
    def lastrowid(self):
        return self._lastrowid

    def __getattr__(self, name):
        return getattr(self.cursor, name)

class SQLiteCompatibleConnection:
    def __init__(self, conn):
        self.conn = conn
        self.row_factory = None 

    def cursor(self):
        # Return a RealDictCursor by default if we want dict access, 
        # but imoveis_web uses sqlite3.Row which is index-based AND key-based.
        # RealDictCursor is key-based only. 
        # psycopg2.extras.DictCursor is index AND key based.
        
        # We need to ensure the pool creates connections with DictCursor factory if possible,
        # or we set it here.
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return SQLiteCompatibleCursor(cur)

    def commit(self):
        return self.conn.commit()
    
    def close(self):
        return self.conn.close() # Actually we shouldn't close if pooled, but `get_conn` callers do close().
        # We need to handle this. If `get_conn` is used, it should release to pool.
        # But existing code calls `conn.close()`. 
        # We can make `close()` call `release_db_connection(self.conn)`.

import psycopg2.extras

def get_compat_conn():
    conn = get_db_connection()
    # We need to patch close to release
    original_close = conn.close
    
    # We wrapper it
    wrapper = SQLiteCompatibleConnection(conn)
    
    # Patch close on wrapper to release
    def release():
        release_db_connection(conn)
    
    wrapper.close = release
    return wrapper

@contextmanager
def get_db(schema=None):
    """
    Context manager to get a DB connection, set schema, and auto-close (release) it.
    """
    conn = get_db_connection()
    try:
        if schema:
            cur = conn.cursor()
            cur.execute(f"SET search_path TO {schema}, public")
            cur.close()
            conn.commit()
        yield conn
    finally:
        release_db_connection(conn)

def close_db(e=None):
    # This is for Flask teardown
    conn = g.pop('db', None)
    if conn is not None:
        release_db_connection(conn)

def init_app(app):
    app.teardown_appcontext(close_db)

