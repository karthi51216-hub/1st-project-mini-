
import mysql.connector
from config import DB_CONFIG

def get_conn():
    return mysql.connector.connect(**DB_CONFIG)

def query(sql, params=None, one=False, commit=False):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    result = None
    if commit:
        conn.commit()
        result = cur.lastrowid
    else:
        result = cur.fetchone() if one else cur.fetchall()
    cur.close()
    conn.close()
    return result