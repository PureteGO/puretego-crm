import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app
from config.database import db_session
from app.models import Project

def link_records():
    app = create_app()
    with app.app_context():
        print("--- Linking Project to Deal ---")
        
        # Hardcoded IDs based on previous check
        project_id = 2
        deal_id = 3
        
        # Use filter instead of get for safer querying
        project = db_session.query(Project).filter(Project.id == project_id).first()
        
        if project:
            print(f"Current Project DealID: {project.deal_id}")
            project.deal_id = deal_id
            db_session.commit()
            
            # Verify update
            updated_project = db_session.query(Project).get(project_id)
            print(f"Updated Project DealID to: {updated_project.deal_id}")
            print("Link established successfully.")
        else:
            print(f"Project with ID {project_id} not found.")

if __name__ == "__main__":
    link_records()
