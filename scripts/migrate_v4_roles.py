import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db_session, engine, Base
from app.models.role import Role, DEFAULT_ROLES

def migrate_roles_v4():
    print("--- Starting Roles V4 Migration ---")
    
    # 1. Update Schema
    print("Checking for missing columns in 'roles' table...")
    new_columns = [
        ('can_manage_gmb', 'TINYINT(1) DEFAULT 0'),
        ('can_manage_healthchecks', 'TINYINT(1) DEFAULT 0'),
        ('can_manage_tickets', 'TINYINT(1) DEFAULT 1')
    ]
    
    try:
        with engine.connect() as conn:
            for col_name, col_type in new_columns:
                result = conn.execute(text(f"SHOW COLUMNS FROM roles LIKE '{col_name}'"))
                if not result.fetchone():
                    print(f"Adding '{col_name}' column to roles...")
                    conn.execute(text(f"ALTER TABLE roles ADD COLUMN {col_name} {col_type}"))
            
            conn.commit()
            print("Schema update successful.")
            
        # 2. Update Role Permissions
        print("Updating Role permissions from DEFAULT_ROLES...")
        session = db_session
        for role_data in DEFAULT_ROLES:
            role = session.query(Role).filter_by(name=role_data['name']).first()
            if not role:
                print(f"Creating Role: {role_data['name']}")
                role = Role(**role_data)
                session.add(role)
            else:
                print(f"Updating permissions for Role: {role_data['name']}")
                for key, value in role_data.items():
                    if hasattr(role, key):
                        setattr(role, key, value)
        
        session.commit()
        print("Roles update successful.")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        raise
    finally:
        db_session.remove()

if __name__ == "__main__":
    migrate_roles_v4()
