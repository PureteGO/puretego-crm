import sys
import os
from sqlalchemy import text

# Add root dir to path
sys.path.append(os.getcwd())

from config.database import engine

def run_migration():
    print("Migrating clients table...")
    with engine.connect() as conn:
        with conn.begin():
            # Helper to add column if not exists (handling via try/catch for simplicity in raw sql or checking schema)
            # Since this is sqlite/mysql, syntax varies. Assuming SQLite for local dev, MySQL for prod.
            # We will try to add columns one by one. If they exist, it might fail, so we wrap.
            
            columns = [
                ("receptionist_name", "VARCHAR(255)"),
                ("decision_maker_name", "VARCHAR(255)"),
                ("decision_factors", "TEXT"),
                ("best_contact_time", "VARCHAR(100)"),
                ("preferred_contact_method", "VARCHAR(100)"),
                ("observations", "TEXT")
            ]
            
            for col_name, col_type in columns:
                try:
                    # SQLite syntax: ALTER TABLE clients ADD COLUMN ...
                    # MySQL syntax: ALTER TABLE clients ADD ...
                    # SQLAlchemy text() allows raw sql.
                    # We will try standard SQL.
                    sql = text(f"ALTER TABLE clients ADD COLUMN {col_name} {col_type}")
                    conn.execute(sql)
                    print(f"Added column {col_name}")
                except Exception as e:
                    print(f"Skipping {col_name} (maybe exists): {e}")

if __name__ == "__main__":
    run_migration()
