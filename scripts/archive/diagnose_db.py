
import sys
import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

# Add current dir to path
sys.path.append(os.getcwd())

load_dotenv()

print("=== PURETEGO CRM - DATABASE DIAGNOSTIC ===")

database_url = os.environ.get('DATABASE_URL')
if not database_url:
    # Try to build from components if DATABASE_URL is missing
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    host = os.environ.get('DB_HOST')
    name = os.environ.get('DB_NAME')
    if all([user, password, host, name]):
        database_url = f"mysql+pymysql://{user}:{password}@{host}/{name}"
    else:
        # Fallback to local SQLite if configured that way
        database_url = "sqlite:///app.db"

print(f"Connecting to: {database_url.split('@')[-1] if '@' in database_url else database_url}")

try:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        from sqlalchemy import text
        res = conn.execute(text("SELECT VERSION()")).fetchone()
        print(f"MySQL Version: {res[0]}")
    
    inspector = inspect(engine)
    
    tables = inspector.get_table_names()
    print(f"\nTables found: {', '.join(tables)}")
    
    if 'clients' in tables:
        print("\nColumns in 'clients' table:")
        columns = inspector.get_columns('clients')
        for col in columns:
            print(f" - {col['name']} ({col['type']})")
            
        required_fields = [
            'receptionist_name', 'decision_maker_name', 'decision_factors', 
            'best_contact_time', 'preferred_contact_method', 'observations',
            'interested_package_id'
        ]
        
        missing = [f for f in required_fields if f not in [c['name'] for c in columns]]
        
        if missing:
            print(f"\n[FAIL] Missing columns in 'clients': {', '.join(missing)}")
        else:
            print("\n[OK] All required columns present in 'clients'.")
            
    if 'service_packages' not in tables:
        print("\n[FAIL] Table 'service_packages' is MISSING.")
    else:
        print("\n[OK] Table 'service_packages' exists.")

    if 'interaction_types' not in tables:
        print("\n[FAIL] Table 'interaction_types' is MISSING.")
    else:
        print("\n[OK] Table 'interaction_types' exists.")
        with engine.connect() as conn:
            from sqlalchemy import text
            count = conn.execute(text("SELECT COUNT(*) FROM interaction_types")).scalar()
            print(f"   - Found {count} interaction types.")
            if count == 0:
                print("   [WARNING] Table 'interaction_types' is EMPTY.")

except Exception as e:
    print(f"\n[ERROR] Database diagnostic failed: {e}")

print("\n=== DIAGNOSTIC END ===")
