
import sys
import os
import requests
import json
import traceback

# Add current dir to path to find app/config
sys.path.append(os.getcwd())

print("=== PURETEGO CRM - PRODUCTION DIAGNOSTIC ===")
print(f"CWD: {os.getcwd()}")
print(f"Python: {sys.version}")

# 1. Test Environment Loading
print("\n1. Testing Environment Variables:")
try:
    from dotenv import load_dotenv
    load_dotenv()
    serpapi_key = os.environ.get('SERPAPI_KEY')
    if serpapi_key:
        print(f"   [OK] SERPAPI_KEY found (length: {len(serpapi_key)})")
        print(f"   [OK] SERPAPI_KEY starts with: {serpapi_key[:5]}...")
    else:
        print("   [FAIL] SERPAPI_KEY NOT FOUND in environment or .env file.")
except Exception as e:
    print(f"   [FAIL] Error loading .env: {e}")

# 2. Test Outbound Connectivity to Google
print("\n2. Testing Outbound Connectivity (Google):")
try:
    resp = requests.get("https://www.google.com", timeout=10)
    print(f"   [OK] Connected to Google. Status: {resp.status_code}")
except Exception as e:
    print(f"   [FAIL] Connection to Google failed: {e}")

# 3. Test Outbound Connectivity to SerpApi
print("\n3. Testing Outbound Connectivity (SerpApi):")
try:
    resp = requests.get("https://serpapi.com/search", timeout=10)
    # 401 is actually a good sign of connectivity (we didn't send a key)
    print(f"   [OK] Connected to SerpApi. Status: {resp.status_code}")
except Exception as e:
    print(f"   [FAIL] Connection to SerpApi failed: {e}")
    if "SSLError" in str(e) or "certificate verify failed" in str(e):
        print("   [TIP] This looks like an SSL CA certificate issue. Some cPanel servers have outdated bundles.")

# 4. Test SerpApi Service specifically
print("\n4. Testing SerpApiService Integration:")
try:
    from app.services import SerpApiService
    serp = SerpApiService()
    print(f"   [OK] SerpApiService initialized.")
    if not serp.api_key:
        print("   [WARNING] SerpApiService initialized with NO API KEY.")
    
    # Test a simple search if key exists
    if serpapi_key:
        print("   Testing simple search for 'Pizza' in Asunción...")
        result = serp.search_business("Pizza", location="Asunción, Paraguay")
        if result:
            print(f"   [OK] Search successful! Title: {result.get('title')}")
        else:
            print("   [FAIL] Search returned no results.")
except Exception as e:
    print(f"   [FAIL] SerpApiService test failed: {e}")
    traceback.print_exc()

print("\n=== DIAGNOSTIC END ===")
