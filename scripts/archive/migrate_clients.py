
from app import create_app
from config.database import get_db
from sqlalchemy import text

app = create_app()

def migrate_clients():
    print("Migrating clients table...")
    with app.app_context():
        with get_db() as db:
            try:
                # Add column
                print("Adding interested_package_id column...")
                db.execute(text("ALTER TABLE clients ADD COLUMN interested_package_id INT"))
                
                # Add foreign key (optional but good practice)
                print("Adding Foreign Key constraint...")
                db.execute(text("ALTER TABLE clients ADD CONSTRAINT fk_clients_package FOREIGN KEY (interested_package_id) REFERENCES service_packages(id) ON DELETE SET NULL"))
                
                db.commit()
                print("Migration successful!")
            except Exception as e:
                print(f"Migration failed (maybe column exists?): {e}")

if __name__ == "__main__":
    migrate_clients()
