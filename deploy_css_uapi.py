import requests
import json
import base64
import os

CPANEL_BASE_URL = "https://puretego.online:2083"
USERNAME = "puretego"
PASSWORD = "Kn16Nt]wB3O:3k"

def upload_file_uapi(local_path, remote_dir):
    print(f"Uploading {local_path} to {remote_dir} via UAPI Fileman...")
    
    url = f"{CPANEL_BASE_URL}/execute/Fileman/upload_files"
    
    with open(local_path, 'rb') as f:
        file_content = f.read()

    files = {
        'file-1': (os.path.basename(local_path), file_content)
    }
    
    data = {
        'dir': remote_dir
    }
    
    try:
        response = requests.post(
            url,
            auth=(USERNAME, PASSWORD),
            data=data,
            files=files,
            verify=True
        )
        response.raise_for_status()
        res_json = response.json()
        
        if res_json.get('status') == 1:
            print("✅ Upload successful via UAPI!")
            print(res_json.get('data', {}))
        else:
            print(f"❌ Upload failed: {res_json}")
    except Exception as e:
        print(f"Error calling API: {e}")
        if 'response' in locals():
            print(response.text)

if __name__ == "__main__":
    upload_file_uapi(
        local_path=r"c:\ProAG\puretego-crm\app\static\css\modules\components.css",
        remote_dir="/home2/puretego/repositories/puretego-crm/app/static/css/modules"
    )
