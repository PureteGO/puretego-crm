import os
import sys
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, os.getcwd())

load_dotenv()

from config.database import db_session
from app.models import GoogleConnection
from app.services.google_business_service import GoogleBusinessService

def debug_locations(connection_id):
    conn = db_session.query(GoogleConnection).get(connection_id)
    if not conn:
        print(f"Connection {connection_id} not found")
        return
        
    service = GoogleBusinessService(conn)
    print(f"Checking accounts for {conn.google_account_email}...")
    
    try:
        accounts = service.list_accounts()
        for account in accounts:
            print(f"\nAccount: {account.get('accountName')} ({account.get('name')})")
            locations = service.list_locations(account['name'])
            for loc in locations:
                print(f"  - Location: {loc.get('title')}")
                print(f"    Name: {loc.get('name')}")
                print(f"    Categories: {loc.get('categories')}")
                print(f"    Metadata: {loc.get('metadata')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # We saw connection_id 2 in the URL in image 2
    debug_locations(2)
