import os
from dotenv import load_dotenv
import pymysql

load_dotenv()

host = os.environ.get('DB_HOST', 'localhost')
user = os.environ.get('DB_USER', 'root')
password = os.environ.get('DB_PASS', '')
db_name = os.environ.get('DB_NAME', 'puretego_crm')

print(f"Testing connection to {user}@{host}/{db_name}...")

try:
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=db_name,
        connect_timeout=5
    )
    print("Connection SUCCESSFUL!")
    conn.close()
except Exception as e:
    print(f"Connection FAILED: {e}")
