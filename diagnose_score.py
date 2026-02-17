import os
import sys
import json
import requests
from flask import Flask

# Add project root to path
sys.path.append(os.getcwd())

from app.services.hasdata_service import HasDataService
from app.services.serpapi_service import SerpApiService
from app.services.serper_service import SerperService

def debug_cess():
    app = Flask(__name__)
    app.config['HASDATA_API_KEY'] = os.environ.get('HASDATA_API_KEY') or ''
    app.config['SERPAPI_KEY'] = os.environ.get('SERPAPI_KEY') or ''
    app.config['SERPER_API_KEY'] = os.environ.get('SERPER_API_KEY') or ''
    
    with app.app_context():
        serper = SerperService()
        hd = HasDataService()
        serp = SerpApiService()
        
        query = "CESS Centro Educativo San Sebastian"
        print(f"--- DIAGNOSING: {query} ---")
        
        # 1. Serper /places
        print("\n1. Testing Serper /places...")
        res_places = serper.search_places(query, country="py")
        if res_places['success'] and res_places.get('places'):
            p = res_places['places'][0]
            print(f"   Found: {p.get('title')} | placeId: {p.get('place_id')} | cid: {p.get('cid')}")
            place_id = p.get('place_id')
            cid = p.get('cid')
        else:
            print("   Serper /places found NOTHING")
            place_id = None
            cid = None

        # 2. Serper /search (Local Pack)
        print("\n2. Testing Serper /search (Local Pack)...")
        res_search = serper.search_local_pack(query, country="py")
        if res_search and 'places' in res_search and res_search['places']:
            p = res_search['places'][0]
            print(f"   Found: {p.get('title')} | placeId: {p.get('placeId')} | cid: {p.get('cid')}")
            if not place_id: place_id = p.get('placeId')
            if not cid: cid = p.get('cid')
        else:
            print("   Serper /search found NOTHING")

        # 3. SerpApi Search
        if not place_id:
            print("\n3. Testing SerpApi Search...")
            res_serp = serp.search_business(query, location="Paraguay")
            if res_serp.get('local_results'):
                p = res_serp['local_results'][0]
                print(f"   Found: {p.get('title')} | place_id: {p.get('place_id')}")
                place_id = p.get('place_id')
            elif res_serp.get('place_results'):
                p = res_serp['place_results']
                print(f"   Found: {p.get('title')} | place_id: {p.get('place_id')}")
                place_id = p.get('place_id')
        
        print(f"\nFINAL IDs: place_id={place_id}, cid={cid}")

        if place_id:
            print("\n4. Testing HasData Details with place_id...")
            hd_det = hd.get_place_details(place_id)
            if hd_det:
                print("   HasData Details Raw Response (First 500 chars):")
                print(json.dumps(hd_det, indent=2)[:500] + "...")
                print(f"\n   Success! Name: {hd_det.get('title')}")
                print(f"   Hours: {bool(hd_det.get('hours') or hd_det.get('workingHours'))}")
                print(f"   Photos: {len(hd_det.get('images', hd_det.get('photos', [])))}")
            else:
                print("   HasData Details FAILED")
        
        if cid:
            print(f"\n5. Testing HasData Reviews with CID: {cid}")
            hd_rev = hd.get_reviews(data_id=cid)
            if hd_rev:
                print(f"   Success! Keys: {list(hd_rev.keys())}")
            else:
                print("   HasData Reviews FAILED")

if __name__ == "__main__":
    debug_cess()
