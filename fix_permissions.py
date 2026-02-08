from app import create_app
from app.models import Role
from config.database import get_db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with get_db() as db:
        print("Checking DB Schema...")
        # Check if column exists
        try:
            db.execute(text("SELECT can_manage_finance FROM roles LIMIT 1"))
            print("Column 'can_manage_finance' already exists.")
        except Exception:
            print("Column 'can_manage_finance' missing. Adding it...")
            try:
                # Determine DB type (assuming sqlite or mysql)
                # For SQLite/MySQL this should work
                db.execute(text("ALTER TABLE roles ADD COLUMN can_manage_finance BOOLEAN DEFAULT 0"))
                db.commit()
                print("Column added successfully.")
            except Exception as e:
                print(f"Failed to add column: {e}")

        # Update Roles
        print("Updating Role Permissions...")
        roles_to_update = ['owner', 'manager', 'finance', 'partner']
        roles = db.query(Role).filter(Role.name.in_(roles_to_update)).all()
        
        for role in roles:
            print(f"Updating {role.name}...")
            role.can_manage_finance = True
        
        db.commit()
        print("Done.")
