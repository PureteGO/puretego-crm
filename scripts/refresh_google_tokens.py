#!/usr/bin/env python
"""
PURETEGO CRM - Token Refresh Script
Refreshes expired Google OAuth tokens.
Run via cron every 30 minutes: */30 * * * * cd /path/to/puretego-crm && python scripts/refresh_google_tokens.py

Author: Maps2GO
"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from config.database import get_db
from app.models import GoogleConnection
from app.routes.google_oauth import refresh_connection_token


def main():
    """Refresh tokens for all connections expiring soon"""
    print(f"[{datetime.now().isoformat()}] Starting token refresh job...")
    
    refreshed = 0
    failed = 0
    skipped = 0
    
    with get_db() as db:
        # Get all active connections
        connections = db.query(GoogleConnection).filter(
            GoogleConnection.is_active == True
        ).all()
        
        print(f"Found {len(connections)} active Google connections")
        
        for conn in connections:
            # Check if token expires within 10 minutes
            if conn.is_token_expired():
                print(f"  Refreshing token for {conn.google_account_email}...")
                
                try:
                    if refresh_connection_token(conn.id):
                        print(f"    ✓ Token refreshed successfully")
                        refreshed += 1
                    else:
                        print(f"    ✗ Failed to refresh token")
                        failed += 1
                except Exception as e:
                    print(f"    ✗ Error: {str(e)}")
                    failed += 1
            else:
                skipped += 1
    
    print(f"\nToken refresh complete:")
    print(f"  Refreshed: {refreshed}")
    print(f"  Failed: {failed}")
    print(f"  Skipped (not expired): {skipped}")
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    exit(main())
