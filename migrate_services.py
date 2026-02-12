from app import create_app
from config.database import get_db
from app.models import Service, ServicePackage, Company

def migrate():
    app = create_app()
    with app.app_context():
        with get_db() as db:
            # Try to find PureteGO
            master = db.query(Company).filter(Company.slug.like('%puretego%')).first()
            if not master:
                # Fallback to ID 1
                master_id = 1
                print("PureteGO not found by slug, using ID 1")
            else:
                master_id = master.id
                print(f"Assigning items to {master.name} (ID: {master_id})")
                
            # Update legacy items
            services_updated = db.query(Service).filter(Service.company_id == None).update({Service.company_id: master_id})
            packages_updated = db.query(ServicePackage).filter(ServicePackage.company_id == None).update({ServicePackage.company_id: master_id})
            
            db.commit()
            print(f"Updated {services_updated} services and {packages_updated} packages.")

if __name__ == "__main__":
    migrate()
