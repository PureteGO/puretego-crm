import os
import json
import requests
import time
from datetime import datetime

# API Keys (Loading from environment or placeholder)
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
HASDATA_API_KEY = os.getenv("HASDATA_API_KEY", "")

LOG_FILE = f"api_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log_result(api_name, status, response_data, error=None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "api": api_name,
        "status": status,
        "error": error,
        "response_summary": str(response_data)[:500] if response_data else None
    }
    print(f"[{api_name}] {status} - {error if error else 'Success'}")
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def test_serper():
    print("Testing Serper API...")
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": "test query"})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        if response.status_code == 200:
            log_result("Serper", "SUCCESS", response.json())
        else:
            log_result("Serper", "FAILED", None, f"Status Code: {response.status_code}, Body: {response.text}")
    except Exception as e:
        log_result("Serper", "ERROR", None, str(e))

def test_serpapi():
    print("Testing SerpApi...")
    url = "https://serpapi.com/search"
    params = {"q": "test query", "api_key": SERPAPI_API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            log_result("SerpApi", "SUCCESS", response.json())
        else:
            log_result("SerpApi", "FAILED", None, f"Status Code: {response.status_code}, Body: {response.text}")
    except Exception as e:
        log_result("SerpApi", "ERROR", None, str(e))

def test_hasdata():
    print("Testing HasData API...")
    url = "https://api.hasdata.com/google/maps/search"
    params = {"q": "restaurant in San Lorenzo, Paraguay"}
    headers = {'x-api-key': HASDATA_API_KEY}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            log_result("HasData", "SUCCESS", response.json())
        else:
            log_result("HasData", "FAILED", None, f"Status Code: {response.status_code}, Body: {response.text}")
    except Exception as e:
        log_result("HasData", "ERROR", None, str(e))

if __name__ == "__main__":
    print(f"Starting API Audit... Results will be saved to {LOG_FILE}")
    test_serper()
    test_serpapi()
    test_hasdata()
    print("Audit Complete.")
