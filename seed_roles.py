from app import create_app
from app.models import Role, DEFAULT_ROLES
from config.database import db_session

app = create_app()

def seed_roles():
    with app.app_context():
        print("Seeding roles...")
        for role_data in DEFAULT_ROLES:
            # Check if role exists
            if not Role.query.filter_by(name=role_data['name']).first():
                print(f"Adding role: {role_data['name']}")
                # Create role, unpacking all fields
                role = Role(**role_data)
                db_session.add(role)
            else:
                print(f"Role already exists: {role_data['name']}")
        
        try:
            db_session.commit()
            print("Roles seeded successfully.")
        except Exception as e:
            db_session.rollback()
            print(f"Error seeding roles: {e}")
        finally:
            db_session.remove()

if __name__ == "__main__":
    seed_roles()
