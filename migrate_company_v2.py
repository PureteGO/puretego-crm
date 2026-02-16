
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST', 'localhost')
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
        
        # Check current columns
        result = conn.execute(text("DESCRIBE companies"))
        existing_columns = [row[0] for row in result]
        
        if 'website' not in existing_columns:
            print("Adding website column...")
            conn.execute(text("ALTER TABLE companies ADD COLUMN website VARCHAR(255)"))
            
        if 'tax_id' not in existing_columns:
            print("Adding tax_id column...")
            conn.execute(text("ALTER TABLE companies ADD COLUMN tax_id VARCHAR(50)"))
            
        if 'email' not in existing_columns:
            print("Adding email column...")
            conn.execute(text("ALTER TABLE companies ADD COLUMN email VARCHAR(255)"))

        conn.commit()
        print("Done.")

except Exception as e:
    print(f"Error: {e}")
