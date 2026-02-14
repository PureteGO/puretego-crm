from app import create_app
from app.models import Project
from config.database import get_db

app = create_app()

with app.app_context():
    with get_db() as db:
        # Fix Patio 1870
        patio = db.query(Project).filter(Project.id == 2).first()
        if patio:
            print(f"Fixing Project 2: {patio.name}")
            patio.total_amount = 2000000.0
            patio.monthly_value = 0.0
            
        # Fix Carniceria
        carniceria = db.query(Project).filter(Project.id == 3).first()
        if carniceria:
            print(f"Fixing Project 3: {carniceria.name}")
            carniceria.total_amount = 3000000.0
            carniceria.monthly_value = 0.0
            
        db.commit()
        print("Local data fixed successfully.")
