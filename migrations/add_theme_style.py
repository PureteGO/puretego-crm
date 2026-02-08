"""
Migration script to add theme_style column to companies table
"""
from config.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE companies ADD COLUMN theme_style VARCHAR(50) DEFAULT 'tech-teal'"))
            conn.commit()
            print("[OK] Column 'theme_style' added to companies table successfully!")
        except Exception as e:
            error_str = str(e).lower()
            if "duplicate column" in error_str or "already exists" in error_str:
                print("[SKIP] Column 'theme_style' already exists - skipping migration")
            else:
                print(f"[ERROR] Migration error: {e}")

if __name__ == "__main__":
    migrate()
