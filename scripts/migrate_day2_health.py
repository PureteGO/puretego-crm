import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db_session, engine
from app.models.health_check import HealthCheck

def migrate_health_checks():
    print("--- Starting Day 2 Health Check Migration ---")
    
    try:
        print("Checking for missing columns...")
        with engine.connect() as conn:
            # Check 'health_checks' table for 'source'
            result = conn.execute(text("SHOW COLUMNS FROM health_checks LIKE 'source'"))
            if not result.fetchone():
                print("Adding 'source' column to health_checks...")
                conn.execute(text("ALTER TABLE health_checks ADD COLUMN source VARCHAR(50) DEFAULT 'official'"))
            
            # Check 'health_checks' table for 'origin_id'
            result = conn.execute(text("SHOW COLUMNS FROM health_checks LIKE 'origin_id'"))
            if not result.fetchone():
                print("Adding 'origin_id' column to health_checks...")
                conn.execute(text("ALTER TABLE health_checks ADD COLUMN origin_id VARCHAR(255) NULL"))
            
            conn.commit()
            print("Migration successful.")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        raise

if __name__ == "__main__":
    migrate_health_checks()
