
from app import create_app
from config.database import get_db
from app.models import ServicePackage

app = create_app()

packages = [
    {
        "name": "Start2GO",
        "price": 1500000.00,
        "description": "Ideal para empreendedores e pequenos comércios.",
        "features": "Perfil Google, Dados essenciais, Carga de serviços, Link de reseñas, Até 3 fotos 360"
    },
    {
        "name": "Biz2GO",
        "price": 2900000.00,
        "description": "Para negócios locais que querem atrair mais tráfego.",
        "features": "Otimização padrão, Landing Page, Integração Maps/WhatsApp, Vídeo Institucional, Até 5 fotos 360"
    },
    {
        "name": "Pro2GO",
        "price": 3900000.00,
        "description": "Para empresas que buscam imagem premium.",
        "features": "Otimização Avançada, Site Institucional (5 seções), SEO Básico, Vídeo Institucional, Até 8 fotos 360"
    },
    {
        "name": "Market2GO",
        "price": 5900000.00,
        "description": "Para negócios que querem começar a vender online.",
        "features": "Site + Catálogo (20 prod), SEO Catálogo, SSL Dedicado, Até 10 fotos 360"
    },
    {
        "name": "e-commerce2GO",
        "price": 7900000.00,
        "description": "Para empresas que desejam uma loja virtual completa.",
        "features": "Loja Virtual (50 prod), Otimização Premium, SEO Completo, Consultoria Domínio, Até 12 fotos 360"
    }
]

def seed_packages():
    print("Seeding Service Packages...")
    with app.app_context():
        with get_db() as db:
            for pkg_data in packages:
                existing = db.query(ServicePackage).filter_by(name=pkg_data['name']).first()
                if not existing:
                    print(f"Creating {pkg_data['name']}")
                    new_pkg = ServicePackage(
                        name=pkg_data['name'],
                        price=pkg_data['price'],
                        description=pkg_data['description'],
                        features=pkg_data['features']
                    )
                    db.add(new_pkg)
                else:
                    print(f"Updating {pkg_data['name']}")
                    existing.price = pkg_data['price']
                    existing.description = pkg_data['description']
                    existing.features = pkg_data['features']
            
            db.commit()
    print("Done!")

if __name__ == "__main__":
    seed_packages()
