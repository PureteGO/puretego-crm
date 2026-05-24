import os
import sys
import json
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def list_locations():
    load_dotenv()
    
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_name = os.getenv('DB_NAME')
    
    db_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Get the VERY LATEST active connection in the whole system to be sure
        print("Checking all active connections...")
        conns = conn.execute(text("SELECT id, google_account_email, access_token FROM google_connections WHERE is_active = 1 ORDER BY id DESC")).all()
        
        for conn_row in conns:
            token = conn_row[2]
            print(f"Testing Connection ID: {conn_row[0]} ({conn_row[1]})")
            headers = {'Authorization': f'Bearer {token}'}
            
            acc_resp = requests.get("https://mybusinessaccountmanagement.googleapis.com/v1/accounts", headers=headers)
            if acc_resp.status_code == 200:
                print(f"!!! FOUND ACTIVE CONNECTION: {conn_row[0]}")
                accounts = acc_resp.json().get('accounts', [])
                for acc in accounts:
                    print(f"Account: {acc.get('name')} | Title: {acc.get('accountName')}")
                    loc_url = f"https://mybusinessbusinessinformation.googleapis.com/v1/{acc.get('name')}/locations?readMask=name,title"
                    loc_resp = requests.get(loc_url, headers=headers)
                    if loc_resp.status_code == 200:
                        locations = loc_resp.json().get('locations', [])
                        for loc in locations:
                            print(f"    Location: {loc.get('name')} | Title: {loc.get('title')}")
                return # Stop at first working connection
            else:
                print(f"  Connection {conn_row[0]} failed: {acc_resp.status_code}")

if __name__ == "__main__":
    list_locations()
