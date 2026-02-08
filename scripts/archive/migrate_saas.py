from app import create_app
from app.models import SaasPackage
from config.database import get_db, Base, engine

app = create_app()

def migrate_saas_packages():
    print("Migrating SaaS Packages...")
    # Create tables directly using metadata
    Base.metadata.create_all(bind=engine)
    print("Tables created/verified.")

    # Seed Data
    with app.app_context():
        with get_db() as db:
            # Check for existing packages
            if db.query(SaasPackage).count() == 0:
                print("Seeding initial packages...")
                
                # Package 1: 10diasFree
                pkg1 = SaasPackage(
                    name="10diasFree",
                    description="Trial de 10 dias com recursos limitados.",
                    price=0.0,
                    max_users=1,
                    max_clients=50,
                    health_check_credits=10
                )
                
                # Package 2: Maps2GOFull
                pkg2 = SaasPackage(
                    name="Maps2GOFull",
                    description="Pacote Completo Ilimitado PureteGO.",
                    price=99.90,
                    max_users=9999, # Effectively unlimited
                    max_clients=999999,
                    health_check_credits=999999
                )
                
                db.add(pkg1)
                db.add(pkg2)
                db.commit()
                print("Packages seeded successfully.")
            else:
                print("Packages already exist.")

if __name__ == "__main__":
    migrate_saas_packages()
