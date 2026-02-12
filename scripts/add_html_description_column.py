
import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import engine

def add_columns():
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Check if columns exist before adding? 
            # Or just try/except. Checking is safer.
            
            # Service
            try:
                conn.execute(text("ALTER TABLE services ADD COLUMN html_description TEXT NULL"))
                print("Added html_description to services.")
            except Exception as e:
                print(f"Error adding to services (might exist): {e}")

            # ServicePackage
            try:
                conn.execute(text("ALTER TABLE service_packages ADD COLUMN html_description TEXT NULL"))
                print("Added html_description to service_packages.")
            except Exception as e:
                print(f"Error adding to service_packages (might exist): {e}")
                
            trans.commit()
            print("Migration completed.")
        except Exception as e:
            trans.rollback()
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    add_columns()
