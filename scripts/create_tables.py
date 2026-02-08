
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import engine, Base
from app.models import * # Import all models to ensure they are registered

def create_tables():
    print("Creating missing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("SUCCESS: Tables created (if they didn't exist).")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    create_tables()
