import sys
import os
# Add current directory to path
sys.path.append(os.getcwd())

from config.database import engine, Base
from sqlalchemy import text
from app.models.project_note import ProjectNote

def run_migration():
    print("Creating project_notes table...")
    try:
        ProjectNote.__table__.create(bind=engine)
        print("project_notes table created.")
    except Exception as e:
        print(f"project_notes table creation skipped (likely exists): {e}")
    
    # Add columns to project_tickets
    print("Adding columns to project_tickets...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE project_tickets ADD COLUMN completed_at DATETIME"))
            print("Added completed_at column.")
        except Exception as e:
            print(f"Error adding completed_at (might exist): {e}")
            
        try:
            conn.execute(text("ALTER TABLE project_tickets ADD COLUMN completed_by INT"))
            conn.execute(text("ALTER TABLE project_tickets ADD CONSTRAINT fk_ticket_completer FOREIGN KEY (completed_by) REFERENCES users(id)"))
            print("Added completed_by column and FK.")
        except Exception as e:
            print(f"Error adding completed_by (might exist): {e}")
            
    print("Migration complete.")

if __name__ == "__main__":
    run_migration()
