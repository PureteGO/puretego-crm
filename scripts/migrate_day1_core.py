import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db_session, engine, Base
from app.models.company import Company
from app.models.user import User
from app.models.client import Client
from app.models.role import Role, DEFAULT_ROLES
from app.utils.saas_limits import PLAN_STRUCTURED
from sqlalchemy import text

def migrate_core():
    print("--- Starting Day 1 Core Migration ---")
    
    # 1. Ensure Tables Exist
    print("Syncing database schema (create_all)...")
    Base.metadata.create_all(bind=engine)
    
    session = db_session
    
    try:
        # 1.5 Manual Schema Migration (ALTER TABLE for existing tables)
        print("Checking for missing columns...")
        with engine.connect() as conn:
            # Check 'companies' table for 'plan_tier'
            result = conn.execute(text("SHOW COLUMNS FROM companies LIKE 'plan_tier'"))
            if not result.fetchone():
                print("Adding 'plan_tier' column to companies...")
                conn.execute(text("ALTER TABLE companies ADD COLUMN plan_tier VARCHAR(50) DEFAULT 'solo'"))
            
            # Check 'companies' table for 'plan_config'
            result = conn.execute(text("SHOW COLUMNS FROM companies LIKE 'plan_config'"))
            if not result.fetchone():
                print("Adding 'plan_config' column to companies...")
                # Note: valid JSON syntax for nullable
                conn.execute(text("ALTER TABLE companies ADD COLUMN plan_config JSON NULL"))
                
            conn.commit()
            
        # 2. Populate Roles
        print("Checking Roles...")
        for role_data in DEFAULT_ROLES:
            role = session.query(Role).filter_by(name=role_data['name']).first()
            if not role:
                print(f"Creating Role: {role_data['name']}")
                role = Role(**role_data)
                session.add(role)
            else:
                # Update permissions if they changed
                print(f"Updating Role: {role_data['name']}")
                for key, value in role_data.items():
                    if hasattr(role, key):
                        setattr(role, key, value)
        session.commit()
        
        # 3. Create Root Tenant (PureteGO)
        print("Checking Root Tenant...")
        root_tenant = session.query(Company).filter_by(slug='puretego').first()
        if not root_tenant:
            print("Creating Root Tenant: PureteGO Agency")
            root_tenant = Company(
                name="PureteGO Agency",
                slug="puretego",
                email="admin@puretego.com",
                plan_tier=PLAN_STRUCTURED
            )
            session.add(root_tenant)
            session.commit()
        else:
            print(f"Root Tenant found: {root_tenant.name}")
            
        # 4. Migrate Users
        print("Migrating Users...")
        users = session.query(User).filter(User.company_id == None).all()
        owner_role = session.query(Role).filter_by(name='owner').first()
        
        for user in users:
            print(f"Assigning User {user.email} to Root Tenant")
            user.company_id = root_tenant.id
            if not user.role_id:
                user.role_id = owner_role.id # Default to Owner for existing users
        
        session.commit()
        
        # 5. Migrate Clients
        print("Migrating Clients...")
        # Update clients where company_id is NULL
        # Using bulk update for efficiency if many clients
        result = session.query(Client).filter(Client.company_id == None).update({Client.company_id: root_tenant.id})
        print(f"Moved {result} clients to Root Tenant.")
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        print(f"CRITICAL ERROR: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate_core()
