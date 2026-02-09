
import os
import sys
import logging
from app import create_app
from config.database import get_db
from app.models import GoogleConnection
from app.services.google_business_service import GoogleBusinessService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_gmb_sync():
    """Debug GMB Sync for the first valid connection found"""
    app = create_app()
    with app.app_context():
        with get_db() as db:
            # Get the most recent connection
            conn = db.query(GoogleConnection).order_by(GoogleConnection.created_at.desc()).first()
            
            if not conn:
                print("No Google Connection found in DB.")
                return

            print(f"--- Debugging Connection ID {conn.id} ({conn.google_account_email}) ---")
            print(f"Scopes: {conn.scopes}")
            print(f"Expires At: {conn.expires_at}")
            
            try:
                service = GoogleBusinessService(conn)
                print("\n1. Listing Accounts...")
                accounts = service.list_accounts()
                print(f"Found {len(accounts)} accounts.")
                
                for acc in accounts:
                    print(f"  - Account: {acc['name']} ({acc['accountName']}) Type: {acc['type']}")
                    
                    print(f"\n2. Listing Locations for {acc['name']}...")
                    try:
                        locations = service.list_locations(acc['name'])
                        print(f"  Found {len(locations)} locations.")
                        for loc in locations:
                            print(f"    - Loc: {loc['title']} (ID: {loc['name']})")
                    except Exception as e:
                        print(f"  ERROR listing locations: {e}")
                        
            except Exception as e:
                print(f"FATAL ERROR: {e}")
                # Print full traceback
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    debug_gmb_sync()
