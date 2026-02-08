import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from config.database import get_db
from sqlalchemy import text

def run_migration():
    print("Starting schema migration...")
    try:
        with get_db() as db:
            print("Altering gmb_location_links table enable nullable client_id...")
            # MySQL syntax modification
            db.execute(text("ALTER TABLE gmb_location_links MODIFY COLUMN client_id INT NULL;"))
            db.commit()
            print("SUCCESS: Table altered.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    run_migration()
