
# import mysql.connector
# from .config import DB_HOST, DB_USER 

# def get_conn():
#     return mysql.connector.connect(host=DB_HOST, user=DB_USER, database="mini_crm")



# def query(sql, params=None, one=False, commit=False):
#     conn = get_conn()
#     cur = conn.cursor(dictionary=True)
#     cur.execute(sql, params or ())
#     result = None
#     if commit:
#         conn.commit()
#         result = cur.lastrowid
#     else:
#         result = cur.fetchone() if one else cur.fetchall()
#     cur.close()
#     conn.close()
#     return result

import mysql.connector
from .config import DB_CONFIG

def get_conn():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        port=DB_CONFIG.get("port", 3306)
    )
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