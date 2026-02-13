import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app
from config.database import db_session
from app.models import Project, Deal

def check_link():
    app = create_app()
    with app.app_context():
        print("--- Checking Project-Deal Link ---")
        
        # 1. Catch the specific Project
        project = db_session.query(Project).filter(
            Project.name.like('%Opmitimización Perfil%')
        ).first()
        
        deal = None # Initialize deal variable

        if project:
            print(f"Project Found: ID={project.id}, Name='{project.name}', DealID={project.deal_id}")
        else:
            print("Project NOT found.")

        # 2. Catch the specific Deal
        deal = db_session.query(Deal).filter(
            Deal.title.like('%Patio de Comidas 1870%')
        ).first()
        
        if deal:
            print(f"Deal Found: ID={deal.id}, Title='{deal.title}'")
        else:
            print("Deal NOT found.")
            
        # 3. Check if they should be linked
        if project and deal:
            if project.deal_id == deal.id:
                print(">>> LINKED CORRECTLY (They are the same entity in logic)")
            else:
                print(">>> NOT LINKED (System treats them as separate sales)")
                print(f"To fix: Set Project(id={project.id}).deal_id = {deal.id}")

if __name__ == "__main__":
    check_link()
