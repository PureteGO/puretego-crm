import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME', 'puretego_crm')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASS', 'Mel_170803$')

def fix_schema():
    # Construct database URL for MySQL
    db_url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            print("Altering tasks table to make due_date nullable...")
            # MySQL syntax
            connection.execute(text("ALTER TABLE tasks MODIFY COLUMN due_date DATETIME NULL;"))
            connection.commit()
            print("Success: tasks.due_date is now nullable.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_schema()
