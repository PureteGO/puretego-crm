import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_db():
    load_dotenv()
    
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_name = os.getenv('DB_NAME')
    
    db_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        print("--- Google Connections ---")
        result = conn.execute(text("SELECT id, google_account_email, is_active, created_at FROM google_connections"))
        for row in result:
            print(f"ID: {row[0]} | Email: {row[1]} | Active: {row[2]} | Created: {row[3]}")
        
        print("\n--- GMB Location Links ---")
        result = conn.execute(text("SELECT id, client_id, google_connection_id, gmb_location_name FROM gmb_location_links"))
        for row in result:
            print(f"ID: {row[0]} | ClientID: {row[1]} | ConnID: {row[2]} | Name: {row[3]}")

if __name__ == "__main__":
    check_db()
