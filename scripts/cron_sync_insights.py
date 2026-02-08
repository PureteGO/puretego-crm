import os
import sys
from datetime import datetime

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import get_db
from app.models import GMBLocationLink, Company
from app.services.google_business_service import GoogleBusinessService, get_service_for_connection

def sync_all_insights():
    """
    Main entry point for cron job to sync GMB insights for all active links.
    """
    print(f"[{datetime.now()}] Starting Bulk GMB Insights Sync...")
    
    with get_db() as db:
        # Get all active location links
        links = db.query(GMBLocationLink).all()
        
        total_synced = 0
        total_errors = 0
        
        for link in links:
            print(f"Syncing link {link.id} for location: {link.gmb_location_name}...")
            try:
                # We need a service instance for the connection
                service = get_service_for_connection(link.google_connection_id)
                
                # Fetch and sync last 30 days
                count = service.sync_insights_to_cache(link.id, days=31)
                print(f"  Result: {count} metrics cached.")
                total_synced += count
                
            except Exception as e:
                print(f"  ERROR syncing link {link.id}: {str(e)}")
                total_errors += 1
                
        print(f"[{datetime.now()}] Bulk Sync Finished.")
        print(f"Total metrics synced: {total_synced}")
        print(f"Total links with errors: {total_errors}")

if __name__ == "__main__":
    sync_all_insights()
