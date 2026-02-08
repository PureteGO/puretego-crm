import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from config.database import get_db, Base
from sqlalchemy import text
from app.models import Client, GMBInsight, Project, ProjectTicket # Trigger import to ensure they are in metadata

def run_migration():
    print("Starting schema migration for Insights and Website...")
    
    with get_db() as db:
        # 1. Create tables if they don't exist (GMBInsight)
        print("Ensuring all tables exist...")
        from config.database import engine
        Base.metadata.create_all(bind=engine)
        
        # 2. Add website column to clients
        print("Checking for website column in clients...")
        try:
            # Check if column exists
            result = db.execute(text("SHOW COLUMNS FROM clients LIKE 'website';"))
            if not result.fetchone():
                print("Adding 'website' column to 'clients' table...")
                db.execute(text("ALTER TABLE clients ADD COLUMN website VARCHAR(255) NULL AFTER email;"))
                db.commit()
                print("SUCCESS: Column 'website' added.")
            else:
                print("Column 'website' already exists.")
        except Exception as e:
            print(f"Error adding column: {e}")
            db.rollback()

if __name__ == "__main__":
    run_migration()
