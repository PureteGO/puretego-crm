import os
import subprocess
from dotenv import load_dotenv
import pymysql

load_dotenv()

DB_USER = os.environ.get('DB_USER', 'root')
DB_PASS = os.environ.get('DB_PASS', '')
DB_NAME = os.environ.get('DB_NAME', 'puretego_crm')

MYSQL_CLI = r"C:\xampp\mysql\bin\mysql.exe"
DUMP_FILE = "app2maps2go_crm-06-03-17-52.sql"

print(f"Dropping and recreating database {DB_NAME}...")

# Use pymysql to drop and recreate the DB
try:
    conn = pymysql.connect(host='localhost', user=DB_USER, password=DB_PASS)
    cursor = conn.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit()
    cursor.close()
    conn.close()
    print("Database recreated successfully.")
except Exception as e:
    print(f"Failed to recreate database: {e}")
    exit(1)

print(f"Importing {DUMP_FILE} using mysql CLI...")

cmd = [MYSQL_CLI, "-u", DB_USER]
if DB_PASS:
    cmd.append(f"-p{DB_PASS}")
cmd.append(DB_NAME)

with open(DUMP_FILE, 'r', encoding='utf-8') as f:
    process = subprocess.Popen(cmd, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    
    if process.returncode != 0:
        print(f"Error importing dump: {err.decode('utf-8', errors='ignore')}")
    else:
        print("Import completed successfully!")
