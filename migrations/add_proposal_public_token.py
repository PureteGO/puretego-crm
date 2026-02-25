"""
Migration script to add public_token column to proposals table
"""
from config.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE proposals ADD COLUMN public_token VARCHAR(100) UNIQUE"))
            conn.commit()
            print("[OK] Column 'public_token' added to proposals table successfully!")
        except Exception as e:
            error_str = str(e).lower()
            if "duplicate column" in error_str or "already exists" in error_str:
                print("[SKIP] Column 'public_token' already exists - skipping migration")
            else:
                print(f"[ERROR] Migration error: {e}")

if __name__ == "__main__":
    migrate()
