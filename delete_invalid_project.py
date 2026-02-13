
from app import create_app
from config.database import get_db
from app.models import Project

app = create_app()

with app.app_context():
    with get_db() as db:
        # Find the project with value 1500 (ID 1 from debug output)
        project = db.query(Project).filter(Project.id == 1).first()
        
        if project:
            print(f"Deleting project: {project.id} - {project.name} (Value: {project.total_amount})")
            db.delete(project)
            db.commit()
            print("Project deleted successfully.")
        else:
            print("Project ID 1 not found.")
