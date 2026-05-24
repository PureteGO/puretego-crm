import requests
try:
    response = requests.get('http://127.0.0.1:5000/services/')
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(response.text[:500])
except Exception as e:
    print(f"Error: {e}")
