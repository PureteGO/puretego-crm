
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
        exit(1)
else:
    print("Using provided DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL)

def add_columns():
    with engine.connect() as conn:
        # Define columns explicitly to check/add
        columns = [
            ("billing_type", "VARCHAR(20) DEFAULT 'recurring'"),
            ("billing_base_day", "INT DEFAULT 10"),
            ("monthly_value", "DECIMAL(12, 2) DEFAULT 0"),
            ("total_amount", "DECIMAL(12, 2) DEFAULT 0"),
            ("financial_status", "VARCHAR(50) DEFAULT 'pending'"), # pending, awaiting_finance, paid, approved
            ("deal_id", "INT DEFAULT NULL"), # Also ensure deal_id foreign key column exists if it was added recently
            ("contract_file_path", "VARCHAR(500) DEFAULT NULL"),
            ("signed_at", "DATETIME DEFAULT NULL")
        ]

        print("Checking/Adding missing columns to 'projects' table...")

        for col_name, col_def in columns:
            try:
                # Check if column exists
                result = conn.execute(text(f"SHOW COLUMNS FROM projects LIKE '{col_name}'"))
                if result.fetchone():
                    print(f" - Column '{col_name}' already exists.")
                else:
                    print(f" - Adding column '{col_name}'...")
                    conn.execute(text(f"ALTER TABLE projects ADD COLUMN {col_name} {col_def}"))
                    conn.commit()
                    print(f"   Success!")
            except Exception as e:
                print(f"   Error processing '{col_name}': {e}")

if __name__ == "__main__":
    add_columns()
