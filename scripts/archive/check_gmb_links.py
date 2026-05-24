import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_links():
    load_dotenv()
    
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_name = os.getenv('DB_NAME')
    
    if not all([db_user, db_pass, db_name]):
        print("Missing DB env vars")
        return

    # Use pymysql
    db_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            print("--- GMB Location Links ---")
            result = conn.execute(text("SELECT id, client_id, gmb_location_name, is_primary FROM gmb_location_links"))
            for row in result:
                print(f"ID: {row[0]} | ClientID: {row[1]} | GMB Name: {row[2]} | Primary: {row[3]}")
            print("--------------------------")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_links()
