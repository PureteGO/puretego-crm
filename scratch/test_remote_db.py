import pymysql
import os

host = "puretego.online"
user = "puretego"
password = "Kn16Nt]wB3O:3k"
db_name = "puretego_puretego_crm"

print(f"Testing connection to {user}@{host}/{db_name}...")

try:
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=db_name,
        connect_timeout=10
    )
    print("Connection SUCCESSFUL!")
    conn.close()
except Exception as e:
    print(f"Connection FAILED: {e}")
