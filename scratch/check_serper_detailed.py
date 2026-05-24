
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def check_serper_detailed():
    print("\n--- Serper.dev Detailed Check ---")
    if not SERPER_API_KEY:
        print("SERPER_API_KEY not found")
        return
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": "test query"})
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        if response.status_code == 200:
            print("Status: SUCCESS")
            print("Response Headers:")
            for k, v in response.headers.items():
                if any(x in k.lower() for x in ['credit', 'usage', 'limit', 'remaining']):
                    print(f"  {k}: {v}")
            
            # Check if credits are in the body
            data = response.json()
            if 'credits' in data:
                print(f"Credits in body: {data['credits']}")
            else:
                print("No credits field in JSON body.")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_serper_detailed()
