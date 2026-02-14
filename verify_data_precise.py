from app import create_app
from app.models import Project, Deal
from config.database import get_db
from datetime import datetime

app = create_app()

with app.app_context():
    with get_db() as db:
        first_day_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        print(f"MONTH_START: {first_day_month}")
        
        projects = db.query(Project).all()
        print("\n--- PROJECTS ---")
        for p in projects:
            print(f"ID:{p.id} | Name:{p.name[:30]} | Setup:{p.total_amount} | Created:{p.created_at} | Status:{p.status}")

        deals = db.query(Deal).filter(Deal.status == 'won').all()
        print("\n--- WON DEALS ---")
        for d in deals:
            p_link = db.query(Project).filter(Project.deal_id == d.id).first()
            print(f"ID:{d.id} | Title:{d.title[:30]} | Value:{d.value} | Updated:{d.updated_at} | ProjID:{p_link.id if p_link else 'None'}")
