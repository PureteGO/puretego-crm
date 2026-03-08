import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_NAME = os.environ.get('DB_NAME', 'puretego_crm')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASS = os.environ.get('DB_PASS', '')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

print(f"Connecting to Local DB: {DB_NAME} at {DB_HOST}...")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Connected.")
        
        result = conn.execute(text("DESCRIBE proposals"))
        columns = [row[0] for row in result]
        
        if 'public_token' not in columns:
            print("Adding public_token column to local proposals table...")
            conn.execute(text("ALTER TABLE proposals ADD COLUMN public_token VARCHAR(100) NULL"))
            conn.execute(text("CREATE UNIQUE INDEX ix_proposals_public_token ON proposals (public_token)"))
            conn.commit()
            print("public_token added successfully.")
        else:
            print("public_token already exists in local DB.")
            
except Exception as e:
    print(f"Error: {e}")
