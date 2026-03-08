import requests
import os
import base64

CPANEL_BASE_URL = "https://puretego.online:2083"
USERNAME = "puretego"
PASSWORD = "Kn16Nt]wB3O:3k"

def run_shell_command(cmd):
    url = f"{CPANEL_BASE_URL}/execute/Shell/run"
    res = requests.get(
        url,
        auth=(USERNAME, PASSWORD),
        params={"command": cmd},
        verify=True
    )
    return res.json()

def deploy_via_shell(local_path, remote_path):
    print(f"Deploying {local_path} -> {remote_path} via Shell API...")
    
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Base64 encode the content to avoid quoting issues in shell
    encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    # Send it to a temporary file via echo and base64 decode, then move it
    cmd = f"echo '{encoded}' | base64 -d > {remote_path}"
    
    res = run_shell_command(cmd)
    print(res)

if __name__ == "__main__":
    deploy_via_shell(
        local_path=r"c:\ProAG\puretego-crm\app\static\css\modules\components.css",
        remote_path="/home2/puretego/repositories/puretego-crm/app/static/css/modules/components.css"
    )
