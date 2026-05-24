
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
HASDATA_API_KEY = os.getenv("HASDATA_API_KEY")

def check_serpapi():
    print("--- SerpApi ---")
    if not SERPAPI_KEY:
        print("SERPAPI_KEY not found")
        return
    url = f"https://serpapi.com/account?api_key={SERPAPI_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"Plan: {data.get('plan_name')}")
            print(f"Total Searches: {data.get('total_searches')}")
            print(f"Searches Per Month: {data.get('searches_per_month')}")
            print(f"Remaining Searches: {data.get('plan_searches_left')}")
            print(f"Account Email: {data.get('account_email')}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def check_serper():
    print("\n--- Serper.dev ---")
    if not SERPER_API_KEY:
        print("SERPER_API_KEY not found")
        return
    # Serper doesn't have a direct credit endpoint, but we can try a simple search and check headers
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": "test"})
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        # Serper returns remaining credits in headers often? Let's check
        # Usually it's in the dashboard, but some APIs provide it.
        # If not, we just check if it's still working.
        if response.status_code == 200:
            print("Status: Active (Connection successful)")
            # print("Headers:", response.headers)
            # Some versions return x-credits-remaining
            for k, v in response.headers.items():
                if 'credit' in k.lower() or 'usage' in k.lower() or 'remaining' in k.lower():
                    print(f"{k}: {v}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def check_hasdata():
    print("\n--- HasData ---")
    if not HASDATA_API_KEY:
        print("HASDATA_API_KEY not found")
        return
    # HasData has an account balance endpoint
    url = "https://api.hasdata.com/account/balance"
    headers = {'x-api-key': HASDATA_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"Remaining Credits: {data.get('credits')}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_serpapi()
    check_serper()
    check_hasdata()
