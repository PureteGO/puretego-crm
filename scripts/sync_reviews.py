#!/usr/bin/env python
"""
PURETEGO CRM - Review Sync Script
Syncs Google Business Profile reviews to local cache.
Run via cron every hour: 0 * * * * cd /path/to/puretego-crm && python scripts/sync_reviews.py

Author: Maps2GO
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from config.database import get_db
from app.models import GMBLocationLink, GoogleConnection
from app.services.google_business_service import GoogleBusinessService


def main():
    """Sync reviews for all linked locations"""
    print(f"[{datetime.now().isoformat()}] Starting review sync job...")
    
    synced = 0
    failed = 0
    skipped = 0
    
    with get_db() as db:
        # Get all location links with active connections
        links = db.query(GMBLocationLink).join(GoogleConnection).filter(
            GoogleConnection.is_active == True
        ).all()
        
        print(f"Found {len(links)} location links to sync")
        
        for link in links:
            try:
                # Check if connection token is valid
                if link.google_connection.is_token_expired():
                    print(f"  Skipping {link.gmb_location_title} - token expired")
                    skipped += 1
                    continue
                
                print(f"  Syncing reviews for {link.gmb_location_title}...")
                
                service = GoogleBusinessService(link.google_connection)
                count = service.sync_reviews_to_cache(link.id)
                
                print(f"    ✓ Synced {count} new reviews")
                synced += count
                
            except Exception as e:
                print(f"    ✗ Error: {str(e)}")
                failed += 1
    
    print(f"\nReview sync complete:")
    print(f"  Reviews synced: {synced}")
    print(f"  Locations failed: {failed}")
    print(f"  Locations skipped: {skipped}")
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    exit(main())
