
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

columns_to_add = [
    ("phone", "VARCHAR(50)"),
    ("website", "VARCHAR(255)"),
    ("address", "TEXT"),
    ("logo_url", "VARCHAR(500)"),
    ("theme_style", "VARCHAR(50) DEFAULT 'tech-teal'"),
    ("currency_symbol", "VARCHAR(5) DEFAULT 'Gs'"),
    ("plan_tier", "VARCHAR(50) DEFAULT 'solo'"),
    ("plan_config", "JSON"),
    ("workflow_mode", "VARCHAR(50) DEFAULT 'lean'"),
    ("commission_closer_rate", "DECIMAL(5, 2) DEFAULT 10.00"),
    ("commission_sdr_rate", "DECIMAL(5, 2) DEFAULT 2.00"),
    ("smtp_server", "VARCHAR(255)"),
    ("smtp_port", "INT DEFAULT 587"),
    ("smtp_use_tls", "BOOLEAN DEFAULT TRUE"),
    ("smtp_username", "VARCHAR(255)"),
    ("smtp_password", "VARCHAR(255)"),
    ("smtp_from_email", "VARCHAR(255)"),
    ("smtp_from_name", "VARCHAR(255)")
]

try:
    with engine.connect() as conn:
        print("Connected.")
        
        # Check current columns
        result = conn.execute(text("DESCRIBE companies"))
        existing_columns = [row[0] for row in result]
        print(f"Existing columns: {existing_columns}")
        
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                print(f"Adding column '{col_name}'...")
                query = f"ALTER TABLE companies ADD COLUMN {col_name} {col_type}"
                conn.execute(text(query))
                print(f"Column '{col_name}' added successfully.")
            else:
                print(f"Column '{col_name}' already exists.")
        
        conn.commit()
        print("\nAll columns checked and updated.")

except Exception as e:
    print(f"\nError: {e}")
