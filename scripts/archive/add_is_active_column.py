import sys
from app import create_app
from sqlalchemy import text
from config.database import get_db

app = create_app()

def add_column():
    print("Checking if 'is_active' column exists in 'clients' table...")
    with app.app_context():
        with get_db() as db:
            # Check if column exists
            try:
                result = db.execute(text("SHOW COLUMNS FROM clients LIKE 'is_active'"))
                column_exists = result.fetchone() is not None
            except Exception as e:
                print(f"Error checking column: {e}")
                return

            if column_exists:
                print("Column 'is_active' already exists.")
            else:
                print("Adding 'is_active' column...")
                try:
                    # Add column with default True (1)
                    db.execute(text("ALTER TABLE clients ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL"))
                    db.commit()
                    print("Column 'is_active' added successfully.")
                except Exception as e:
                    print(f"Error adding column: {e}")
                    db.rollback()

if __name__ == "__main__":
    add_column()
