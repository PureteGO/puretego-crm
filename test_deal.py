import sys
from app import create_app
from config.database import get_db
from app.models import Deal, DealStatus, Client
from datetime import datetime

app = create_app()
with app.app_context():
    with get_db() as db:
        print("Creating deal...")
        client = db.query(Client).first()
        if not client:
            print("No clients found")
            sys.exit(1)
        
        try:
            deal = Deal(
                title='Test Deal',
                company_id=1,
                client_id=client.id,
                kanban_stage_id=1,
                owner_id=1,
                value=100.0,
            )
            deal.status = DealStatus.OPEN
            db.add(deal)
            db.commit()
            print("Deal created successfully!")
        except Exception as e:
            print(f"Failed to create deal: {e}")
            raise
