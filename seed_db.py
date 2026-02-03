from app import create_app
from app.models import User, KanbanStage, Service
from config.database import db_session
import bcrypt

app = create_app()

def seed():
    with app.app_context():
        print("Seeding database...")
        
        # 1. Kanban Stages
        stages = [
            ('Primeiro Contato', 1),
            ('Visita Agendada', 2),
            ('Proposta Enviada', 3),
            ('Negociação', 4),
            ('Fechado - Ganho', 5),
            ('Fechado - Perdido', 6)
        ]
        
        for name, order in stages:
            if not KanbanStage.query.filter_by(name=name).first():
                stage = KanbanStage(name=name, order=order)
                db_session.add(stage)
        
        # 2. Services
        services = [
            (
                'Dominación en Google Maps - Pack 90 días', 
                'Auditoría SEO Local avanzada, optimización técnica del Perfil de Empresa (GMB), gestión estratégica de reseñas y reputación, y posicionamiento en el Local Pack para máxima visibilidad.', 
                3500000.00
            ),
            (
                'Desarrollo Web de Alto Nivel', 
                'Sitios enfocados en la conversión (CRO) y optimizados para Google. Diseño personalizado, velocidad extrema, adaptado a móviles y con DNS gestionado profesionalmente.', 
                3500000.00
            ),
            (
                'Tienda Virtual de Gran Escala', 
                'E-commerce profesional con gestión de inventario, pasarela de pagos integrada y optimización para ventas masivas online. Incluye seguimiento de conversiones.', 
                7500000.00
            ),
            (
                'Propulsor de Tráfico (Google Ads)',
                'Gestión de campañas SEM focalizadas en intención de compra. Segmentación avanzada para atraer clientes calificados de forma inmediata y maximizar el ROI.',
                2500000.00
            )
        ]
        
        for name, desc, price in services:
            if not Service.query.filter_by(name=name).first():
                service = Service(name=name, description=desc, base_price=price)
                db_session.add(service)

        # 3. Admin User
        admin_email = 'admin@puretego.online'
        if not User.query.filter_by(email=admin_email).first():
            print(f"Creating admin user: {admin_email}")
            # The model handles hashing in set_password
            admin = User(name='Administrador', email=admin_email, password='nopasswordyet') 
            # We need to manually set the password to match the known hash OR just set a new known password.
            # Let's set the 'admin123' password using the model's method which generates a compatible bcrypt hash.
            admin.set_password('admin123')
            db_session.add(admin)
        else:
            print("Admin user already exists.")

        try:
            db_session.commit()
            print("Database seeded successfully!")
        except Exception as e:
            db_session.rollback()
            print(f"Error seeding database: {e}")
        finally:
            db_session.remove()

if __name__ == '__main__':
    seed()
