
from app import create_app
from app.models import Client, Interaction
from config.database import get_db

app = create_app()

with app.app_context():
    with get_db() as db:
        clients = db.query(Client).all()
        print(f"Total Clients: {len(clients)}")
        for c in clients:
            count = db.query(Interaction).filter_by(client_id=c.id).count()
            print(f"Client: {c.name} (ID: {c.id}) - Interactions: {count}")
