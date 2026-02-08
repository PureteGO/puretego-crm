
import sys
import os
from flask import Flask

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.google_business_service import GoogleBusinessService
from app.models import GoogleConnection
from config.database import get_db

def verify_locations():
    """Verify fetching locations for all connected accounts"""
    # Initialize minimal Flask app for context if needed (though we just need DB)
    from app import create_app
    app = create_app()
    
    with app.app_context():
        with get_db() as db:
            connections = db.query(GoogleConnection).filter(GoogleConnection.is_active == True).all()
            
            if not connections:
                print("No active Google connections found.")
                return

            print(f"Found {len(connections)} active connections.")
            
            for conn in connections:
                print(f"\nChecking connection: {conn.google_account_email} (ID: {conn.id})")
                
                try:
                    service = GoogleBusinessService(conn)
                    print("Initialized service.")
                    
                    accounts = service.list_accounts()
                    print(f"Accounts found: {len(accounts)}")
                    
                    for acc in accounts:
                        print(f"  - Account: {acc['name']} ({acc['accountName']}) - Type: {acc.get('type')} - Role: {acc.get('role')}")
                        
                        try:
                            locations = service.list_locations(acc['name'])
                            print(f"    Locations ({len(locations)}):")
                            for loc in locations:
                                print(f"      * {loc['title']} ({loc['name']})")
                                print(f"        Address: {loc['address']}")
                        except Exception as loc_err:
                            print(f"    ERROR fetching locations for account {acc['name']}: {loc_err}")
                            
                except Exception as e:
                    print(f"ERROR processing connection {conn.google_account_email}: {e}")

if __name__ == "__main__":
    verify_locations()
