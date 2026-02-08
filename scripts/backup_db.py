import os
import subprocess
import shutil
from datetime import datetime
from dotenv import load_dotenv

def backup_db():
    # Load .env variables
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)

    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'puretego_crm')
    db_host = os.getenv('DB_HOST', 'localhost')

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), f"FULL_DB_BACKUP_PRE_REFACTOR_{timestamp}.sql")

    # Possible paths for mysqldump
    possible_paths = [
        "mysqldump", # If it's in PATH
        r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
        r"C:\xampp\mysql\bin\mysqldump.exe",
        r"C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
    ]

    mysqldump_cmd = None
    for path in possible_paths:
        if shutil.which(path) or os.path.exists(path):
            mysqldump_cmd = path
            break
    
    if not mysqldump_cmd:
        print("CRITICAL ERROR: mysqldump.exe not found in common locations.")
        return

    print(f"Using mysqldump from: {mysqldump_cmd}")
    print(f"Backing up database '{db_name}' to: {backup_file}")

    cmd = [
        mysqldump_cmd,
        "-h", db_host,
        "-u", db_user,
        f"--password={db_pass}",
        "--databases", db_name,
        "--single-transaction",
        "--quick",
        "--lock-tables=false",
        f"--result-file={backup_file}"
    ]

    try:
        # Run command
        # Note: Parsing password directly in command list avoids shell injection, but on Windows with subprocess it can be tricky depending on how it's handled. 
        # However, subprocess.run with a list of args is generally safe.
        subprocess.run(cmd, check=True, shell=True) 
        # shell=True is often needed on Windows for path resolution if not full path, but here we might have full path.
        # Let's try shell=True to be safe with environment.
        
        if os.path.exists(backup_file) and os.path.getsize(backup_file) > 0:
            print("Database backup successful!")
        else:
             print("Backup file created but appears empty or missing.")

    except subprocess.CalledProcessError as e:
        print(f"Error executing mysqldump: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    backup_db()
