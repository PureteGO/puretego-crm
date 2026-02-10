
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Force localhost
DB_HOST = 'localhost'
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_NAME = os.environ.get('DB_NAME', 'puretego_crm')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASS = os.environ.get('DB_PASS', '')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

print(f"Connecting to: {DATABASE_URL}")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Connected.")
        
        # Check if columns exist first
        print("Checking columns...")
        result = conn.execute(text("DESCRIBE clients"))
        columns = [row[0] for row in result]
        
        if 'funnel_start_date' not in columns:
            print("Adding funnel_start_date column...")
            conn.execute(text("ALTER TABLE clients ADD COLUMN funnel_start_date DATETIME DEFAULT CURRENT_TIMESTAMP"))
            print("funnel_start_date added.")
        else:
            print("funnel_start_date already exists.")

        if 'status' not in columns:
            print("Adding status column...")
            conn.execute(text("ALTER TABLE clients ADD COLUMN status VARCHAR(50) DEFAULT 'lead'"))
            print("status added.")
        else:
            print("status already exists.")
            
        conn.commit()
        print("Done.")

except Exception as e:
    print(f"Error: {e}")
