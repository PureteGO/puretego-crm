from app import create_app
from app.models import Client
from config.database import get_db

print("Attempting to create app...")
try:
    app = create_app()
    print("App created successfully.")
    
    print("Attempting to push app context...")
    with app.app_context():
        print("Context pushed.")
        with get_db() as db:
            print("Database connection successful.")
            # Check if we can query Client with the new field
            try:
                c = db.query(Client).first()
                print("Client query successful.")
                if c:
                    print(f"Client found: {c.name}, active: {c.is_active}")
            except Exception as e:
                print(f"Error querying client: {e}")
                raise
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
