from config.database import engine
from sqlalchemy import text

def migrate():
    print("Starting migration for partial payments...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE receivables ADD COLUMN paid_amount DECIMAL(12, 2) DEFAULT 0;"))
            print("Added paid_amount to receivables")
        except Exception as e:
            print(f"Receivables: {e}")
            
        try:
            conn.execute(text("ALTER TABLE payables ADD COLUMN paid_amount DECIMAL(12, 2) DEFAULT 0;"))
            print("Added paid_amount to payables")
        except Exception as e:
            print(f"Payables: {e}")
        
        conn.commit()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()
