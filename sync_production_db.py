import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

# DB Config from .env
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'puretego_crm')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASS = os.environ.get('DB_PASS', '')

dump_file = 'app2maps2go_crm.sql'

# Potential mysql.exe paths
paths = [
    r"C:\xampp\mysql\bin\mysql.exe",
    r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
    r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe",
]

mysql_exe = "mysql" # fallback if in path
for p in paths:
    if os.path.exists(p):
        mysql_exe = f'"{p}"'
        print(f"Found MySQL at: {p}")
        break

# Drop and recreate database for a clean import
drop_create_cmd = f'{mysql_exe} -h{DB_HOST} -P{DB_PORT} -u{DB_USER} -p"{DB_PASS}" -e "DROP DATABASE IF EXISTS {DB_NAME}; CREATE DATABASE {DB_NAME};"'
print(f"Recreating database: {DB_NAME}")
subprocess.run(drop_create_cmd, shell=True, check=True)

command = f'{mysql_exe} -h{DB_HOST} -P{DB_PORT} -u{DB_USER} -p"{DB_PASS}" {DB_NAME} < {dump_file}'

print(f"Executing: {command.replace(DB_PASS, '********')}")

try:
    # Use shell=True for input redirection on Windows
    result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
    print("Import successful!")
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print(f"Error during import: {e}")
    print(e.stderr)
