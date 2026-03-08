import requests
import os

CPANEL_BASE_URL = "https://puretego.online:2083"
USERNAME = "puretego"
PASSWORD = "Kn16Nt]wB3O:3k"

def upload_file_to_cpanel(local_path, remote_dir, remote_file):
    print(f"Uploading {local_path} to {remote_dir}/{remote_file}...")
    
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    res_upload = requests.post(
        f"{CPANEL_BASE_URL}/execute/Fileman/save_file_content",
        auth=(USERNAME, PASSWORD),
        data={
            "dir": remote_dir,
            "file": remote_file,
            "content": content,
            "from_charset": "utf-8",
            "to_charset": "utf-8"
        }
    )
    
    try:
        data = res_upload.json()
        if data.get('status') == 1:
            print("✅ Upload successful!")
        else:
            print(f"❌ Upload failed: {data}")
    except Exception as e:
        print(f"❌ Error parsing response: {e}, Response: {res_upload.text}")

if __name__ == "__main__":
    upload_file_to_cpanel(
        local_path=r"c:\ProAG\puretego-crm\app\static\css\modules\dark-mode-fixes.css",
        remote_dir="repositories/puretego-crm/app/static/css/modules",
        remote_file="dark-mode-fixes.css"
    )
    
    upload_file_to_cpanel(
        local_path=r"c:\ProAG\puretego-crm\app\templates\base.html",
        remote_dir="repositories/puretego-crm/app/templates",
        remote_file="base.html"
    )
    
    # Touch restart.txt
    print("\nRestarting Python app via Passenger touch...")
    res_shell = requests.get(
        f"{CPANEL_BASE_URL}/execute/Shell/run",
        auth=(USERNAME, PASSWORD),
        params={"command": "mkdir -p /home2/puretego/repositories/puretego-crm/tmp && touch /home2/puretego/repositories/puretego-crm/tmp/restart.txt"}
    )
    print(res_shell.json())
