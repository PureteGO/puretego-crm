
import os
import requests
from dotenv import load_dotenv

load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def check_serper_account():
    print("--- Serper Account Check ---")
    if not SERPER_API_KEY:
        print("SERPER_API_KEY not found")
        return
    
    # Try common account endpoints
    endpoints = [
        "https://google.serper.dev/account",
        "https://api.serper.dev/account"
    ]
    
    headers = {'X-API-KEY': SERPER_API_KEY}
    
    for url in endpoints:
        try:
            print(f"Trying {url}...")
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"Success: {response.json()}")
            else:
                print(f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_serper_account()
