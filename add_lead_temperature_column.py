
import sqlalchemy as sa
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    # Fallback to individual variables (common in cPanel/MySQL)
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '3306')
    name = os.getenv('DB_NAME', 'puretego_crm')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASS', '')
    
    if user and password and name:
        DATABASE_URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"
        print(f"Using constructed DATABASE_URL for {host}")
    else:
        print("Error: DATABASE_URL not found and DB_* variables incomplete.")
        print("Loaded variables (masked):")
        print(f"DB_HOST={host}")
        print(f"DB_USER={user}")
        print(f"DB_NAME={name}")
        exit(1)
else:
    print("Using provided DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL)

def add_column():
    with engine.connect() as conn:
        # Check if column exists
        try:
            result = conn.execute(text("SHOW COLUMNS FROM clients LIKE 'lead_temperature'"))
            if result.fetchone():
                print("Column 'lead_temperature' already exists.")
                return
        except Exception as e:
            print(f"Error checking column: {e}")
            return

        # Add column
        print("Adding 'lead_temperature' column to 'clients' table...")
        try:
            conn.execute(text("ALTER TABLE clients ADD COLUMN lead_temperature VARCHAR(20) DEFAULT 'cold'"))
            conn.commit()
            print("Column added successfully!")
        except Exception as e:
            print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_column()
