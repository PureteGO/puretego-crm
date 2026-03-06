"""
Migration: Add scan_token column to users table
For GBP Scan bookmarklet/extension authentication
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine
from sqlalchemy import text, inspect

def migrate():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    with engine.connect() as conn:
        if 'scan_token' not in columns:
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN scan_token VARCHAR(64) UNIQUE
            """))
            conn.commit()
            print("✅ Column 'scan_token' added to users table")
        else:
            print("ℹ️  Column 'scan_token' already exists")
    
    # Create index if not exists
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_users_scan_token ON users (scan_token)
            """))
            conn.commit()
            print("✅ Index on scan_token created")
        except Exception as e:
            print(f"ℹ️  Index may already exist: {e}")

if __name__ == '__main__':
    migrate()
