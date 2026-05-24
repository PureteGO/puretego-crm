"""
Migration script to add stage_updated_at columns to clients and deals tables,
and modify deals.status enum values to include 'inactive'.
"""
import os
from sqlalchemy import text
from config.database import engine

def migrate():
    # Detect dialect
    is_sqlite = engine.dialect.name == 'sqlite'
    print(f"Running migration on database dialect: {engine.dialect.name}")

    with engine.connect() as conn:
        # 1. Add stage_updated_at to clients table
        try:
            conn.execute(text("ALTER TABLE clients ADD COLUMN stage_updated_at DATETIME NULL"))
            conn.commit()
            print("[OK] Column 'stage_updated_at' added to 'clients' table.")
        except Exception as e:
            if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                print("[SKIP] Column 'stage_updated_at' already exists in 'clients' table.")
            else:
                print(f"[ERROR] clients.stage_updated_at: {e}")

        # 2. Add stage_updated_at to deals table
        try:
            conn.execute(text("ALTER TABLE deals ADD COLUMN stage_updated_at DATETIME NULL"))
            conn.commit()
            print("[OK] Column 'stage_updated_at' added to 'deals' table.")
        except Exception as e:
            if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                print("[SKIP] Column 'stage_updated_at' already exists in 'deals' table.")
            else:
                print(f"[ERROR] deals.stage_updated_at: {e}")

        # 3. Update status enum in deals table (MySQL only)
        if not is_sqlite:
            try:
                conn.execute(text("ALTER TABLE deals MODIFY COLUMN status ENUM('open', 'won', 'lost', 'inactive') DEFAULT 'open'"))
                conn.commit()
                print("[OK] Enum values in 'deals.status' updated successfully.")
            except Exception as e:
                print(f"[ERROR] Modifying 'deals.status' enum: {e}")

        # 4. Initialize stage_updated_at values to updated_at or created_at
        try:
            conn.execute(text("UPDATE clients SET stage_updated_at = COALESCE(updated_at, created_at) WHERE stage_updated_at IS NULL"))
            conn.execute(text("UPDATE deals SET stage_updated_at = COALESCE(updated_at, created_at) WHERE stage_updated_at IS NULL"))
            conn.commit()
            print("[OK] Initialized 'stage_updated_at' values for existing clients and deals.")
        except Exception as e:
            print(f"[ERROR] Initializing stage_updated_at: {e}")

if __name__ == "__main__":
    migrate()
