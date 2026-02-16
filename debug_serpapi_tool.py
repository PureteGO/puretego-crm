from app import create_app
from app.services.serpapi_service import SerpApiService
import json
import os

app = create_app()

with app.app_context():
    service = SerpApiService()
    # Test with the known client
    business_name = "CESS Centro Educativo San Sebastian"
    location = "San Lorenzo, Paraguay" # Guessing location based on context or use default
    
    print(f"Searching for: {business_name}...")
    result = service.analyze_gmb_profile(business_name)
    
    print(f"Score: {result.get('score')}")
    print("Criteria details:")
    for c in result['report']['criteria']:
        print(f" - {c['name_es']} (ID {c['id']}): {c['status']} (Score: {c['score']}) [{c['message']}]")
    
    # Dump raw result to file for inspection
    raw_debug_file = 'debug_serpapi_result.json'
    with open(raw_debug_file, 'w', encoding='utf-8') as f:
        # We can't easily access the raw_data variable from analyze_gmb_profile since it returns a processed dict
        # So we'll manually call search_business to inspect raw data
        print("\nFetching raw data for inspection...")
        raw = service.search_business(business_name)
        json.dump(raw, f, indent=2, ensure_ascii=False)
    
    print(f"\nRaw data saved to {raw_debug_file}")

    # Specific checks
    if 'local_results' in raw and raw['local_results']:
        item = raw['local_results'][0]
        print(f"\n--- Raw Item Checks ---")
        print(f"Verification status (verified): {item.get('verified')}")
        print(f"Photos count: {len(item.get('photos', []))}")
        print(f"Extensions/Tags in photos: {[str(p).lower() for p in item.get('photos', [])[:3]]}") # Sample
    
