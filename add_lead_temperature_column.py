
import sqlalchemy as sa
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL not found in .env")
    exit(1)

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
