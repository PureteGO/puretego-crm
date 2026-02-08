from app import create_app
from sqlalchemy import text
from config.database import get_db

app = create_app()

def add_currency_column():
    print("Checking if 'currency_symbol' column exists in 'companies' table...")
    with app.app_context():
        with get_db() as db:
            # Check if column exists
            try:
                result = db.execute(text("SHOW COLUMNS FROM companies LIKE 'currency_symbol'"))
                column_exists = result.fetchone() is not None
            except Exception as e:
                print(f"Error checking column: {e}")
                return

            if column_exists:
                print("Column 'currency_symbol' already exists.")
            else:
                print("Adding 'currency_symbol' column...")
                try:
                    # Add column with default 'Gs'
                    db.execute(text("ALTER TABLE companies ADD COLUMN currency_symbol VARCHAR(5) DEFAULT 'Gs'"))
                    db.commit()
                    print("Column 'currency_symbol' added successfully.")
                except Exception as e:
                    print(f"Error adding column: {e}")
                    db.rollback()

if __name__ == "__main__":
    add_currency_column()
