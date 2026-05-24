import os
import sys
import json
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_location_details():
    load_dotenv()
    
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_name = os.getenv('DB_NAME')
    
    db_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Get connection info for client 41
        result = conn.execute(text("""
            SELECT gc.access_token, gll.gmb_location_name 
            FROM gmb_location_links gll
            JOIN google_connections gc ON gll.google_connection_id = gc.id
            WHERE gll.client_id = 41
        """)).first()
        
        if not result:
            print("Connection not found for client 41")
            return
            
        token, location_name = result
        print(f"Testing location: {location_name}")
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # Try to get the location details from the Information API
        # URL pattern: https://mybusinessbusinessinformation.googleapis.com/v1/{name}
        info_url = f"https://mybusinessbusinessinformation.googleapis.com/v1/{location_name}"
        
        print(f"Calling Information API: {info_url}")
        resp = requests.get(info_url, headers=headers)
        print(f"Response Status: {resp.status_code}")
        if resp.status_code == 200:
            print("Location details found!")
            print(json.dumps(resp.json(), indent=2))
        else:
            print(f"Error: {resp.text}")

if __name__ == "__main__":
    get_location_details()
