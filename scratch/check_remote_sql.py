import requests
import json

CPANEL_BASE_URL = "https://puretego.online:2083"
USERNAME = "puretego"
PASSWORD = "Kn16Nt]wB3O:3k"

def cpanel_api(module, function, params=None):
    if params is None:
        params = {}
    url = f"{CPANEL_BASE_URL}/execute/{module}/{function}"
    try:
        response = requests.get(url, auth=(USERNAME, PASSWORD), params=params, verify=True)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error calling API: {e}")
        return None

print("Reading gbpcheck_old/run.py...")
res = cpanel_api("Fileman", "get_file_content", {
    "dir": "gbpcheck_old",
    "file": "run.py"
})
if res and res.get('status') == 1:
    print(res['data']['content'])
else:
    print("Could not read run.py.")
