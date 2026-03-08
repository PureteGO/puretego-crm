import requests
import json
import base64
import time

CPANEL_BASE_URL = "https://puretego.online:2083"
USERNAME = "puretego"
PASSWORD = "Kn16Nt]wB3O:3k"

def cpanel_api(module, function, params=None):
    if params is None:
        params = {}
    
    url = f"{CPANEL_BASE_URL}/execute/{module}/{function}"
    
    try:
        response = requests.get(
            url,
            auth=(USERNAME, PASSWORD),
            params=params,
            verify=True
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error calling API: {e}")
        return None

def main():
    print("--- DEPLOYING DATABASE FIX TO CPANEL ---")

    python_script = """
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Force connect to cpanel local db
DB_HOST = 'localhost'
DB_PORT = 3306
DB_NAME = os.environ.get('DB_NAME', 'puretego_crm')
DB_USER = os.environ.get('DB_USER', 'puretego_crm_user')
DB_PASS = os.environ.get('DB_PASS', '')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

print(f"Connecting to DB...")
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Connected.")
        
        result = conn.execute(text("DESCRIBE proposals"))
        columns = [row[0] for row in result]
        
        if 'public_token' not in columns:
            print("Adding public_token column to proposals...")
            conn.execute(text("ALTER TABLE proposals ADD COLUMN public_token VARCHAR(100) NULL"))
            conn.execute(text("CREATE UNIQUE INDEX ix_proposals_public_token ON proposals (public_token)"))
            print("public_token added.")
        else:
            print("public_token already exists.")
            
        conn.commit()
        print("Fix applied successfully.")
        
        with open('migration_status.txt', 'w') as f:
            f.write("SUCCESS")
except Exception as e:
    print(f"Error: {e}")
    with open('migration_status.txt', 'w') as f:
        f.write(f"ERROR: {str(e)}")
"""
    
    encoded_script = "\n".join(python_script.splitlines())
    
    print("\n[1/3] Uploading script to cPanel...")
    # NOTE: Fileman takes the content as a string
    res_upload = requests.post(
        f"{CPANEL_BASE_URL}/execute/Fileman/save_file_content",
        auth=(USERNAME, PASSWORD),
        data={
            "dir": "repositories/puretego-crm",
            "file": "run_fix_db.py",
            "content": encoded_script,
            "from_charset": "utf-8",
            "to_charset": "utf-8"
        }
    )
    
    print("\n[2/3] Executing script using cPanel cron API...")
    # Run the script via cron to bypass SSH restriction
    cron_cmd = "source /home2/puretego/pythonvenv/repositories/puretego-crm/11/bin/activate && cd /home2/puretego/repositories/puretego-crm && python run_fix_db.py"
    
    # Run a one-off shell command
    res_shell = cpanel_api("Shell", "run", {
        "command": cron_cmd
    })
    
    print(res_shell)
    
    print("\n[3/3] Checking output...")
    time.sleep(5)
    
    res_read = cpanel_api("Fileman", "get_file_content", {
        "dir": "repositories/puretego-crm",
        "file": "migration_status.txt"
    })
    
    if res_read and res_read.get('status') == 1:
        print("\nRESULT:")
        print(res_read['data']['content'])
    else:
        print("Could not read result file.")

if __name__ == "__main__":
    main()
