import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db_session, engine, Base

def full_schema_check():
    print("--- Starting Full Schema Check & Migration ---")
    
    # 1. Ensure all base tables exist first
    print("Syncing base schema (create_all)...")
    Base.metadata.create_all(bind=engine)
    
    # Table and their expected columns (name, type_sql)
    migrations = {
        'roles': [
            ('can_manage_gmb', 'TINYINT(1) DEFAULT 0'),
            ('can_manage_healthchecks', 'TINYINT(1) DEFAULT 0'),
            ('can_manage_tickets', 'TINYINT(1) DEFAULT 1')
        ],
        'companies': [
            ('smtp_server', 'VARCHAR(255) NULL'),
            ('smtp_port', 'INTEGER DEFAULT 587'),
            ('smtp_use_tls', 'TINYINT(1) DEFAULT 1'),
            ('smtp_username', 'VARCHAR(255) NULL'),
            ('smtp_password', 'VARCHAR(255) NULL'),
            ('smtp_from_email', 'VARCHAR(255) NULL'),
            ('smtp_from_name', 'VARCHAR(255) NULL'),
            ('logo_url', 'VARCHAR(500) NULL'),
            ('theme_style', "VARCHAR(50) DEFAULT 'tech-teal'"),
            ('currency_symbol', "VARCHAR(5) DEFAULT 'Gs'"),
            ('is_active', 'TINYINT(1) DEFAULT 1'),
            ('plan_tier', "VARCHAR(50) DEFAULT 'solo'"),
            ('plan_config', 'JSON NULL')
        ],
        'users': [
            ('is_superadmin', 'TINYINT(1) DEFAULT 0'),
            ('reset_token', 'VARCHAR(100) NULL'),
            ('reset_token_expires', 'DATETIME NULL'),
            ('is_active', 'TINYINT(1) DEFAULT 1')
        ],
        'projects': [
            ('financial_status', "VARCHAR(50) DEFAULT 'pending'"),
            ('phase', "VARCHAR(50) DEFAULT 'vendas'"),
            ('contract_file_path', 'VARCHAR(500) NULL'),
            ('signed_at', 'DATETIME NULL'),
            ('deal_id', 'INTEGER NULL')
        ],
        'project_tickets': [
            ('phase', 'VARCHAR(50) NULL'),
            ('is_onboarding', 'TINYINT(1) DEFAULT 0')
        ]
    }
    
    try:
        with engine.connect() as conn:
            for table_name, columns in migrations.items():
                print(f"Checking table: {table_name}")
                for col_name, col_type in columns:
                    result = conn.execute(text(f"SHOW COLUMNS FROM {table_name} LIKE '{col_name}'"))
                    if not result.fetchone():
                        print(f"  -> Adding '{col_name}' to {table_name}...")
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                    else:
                        print(f"  -> Column '{col_name}' already exists.")
            
            conn.commit()
            print("\nFull Schema Migration successful.")
            
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        raise
    finally:
        db_session.remove()

if __name__ == "__main__":
    full_schema_check()
