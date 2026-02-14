from app import create_app
from app.models import Project, Deal
from config.database import get_db
from sqlalchemy import func
from datetime import datetime

app = create_app()

with app.app_context():
    with get_db() as db:
        first_day_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        print(f"Checking records from: {first_day_month}")

        # 1. Projects (Setup Value Only)
        projects = db.query(Project).filter(
            Project.status != 'cancelled',
            Project.created_at >= first_day_month
        ).all()
        
        print("\n--- Projects (Created this month) ---")
        total_projects = 0
        for p in projects:
            val = float(p.total_amount or 0)
            total_projects += val
            print(f"Project: {p.name} (Client: {p.client.name}) - Setup Amount: {val}")

        # 2. Deals (Won, no project)
        deals = db.query(Deal).filter(
            Deal.status == 'won',
            Deal.updated_at >= first_day_month,
            ~Deal.id.in_(db.query(Project.deal_id).filter(Project.deal_id != None))
        ).all()
        
        print("\n--- Deals (Won this month, no project) ---")
        total_deals = 0
        for d in deals:
            total_deals += d.value
            print(f"Deal: {d.title} (Client: {d.client.name}) - Value: {d.value}")
            
        print(f"\nTotal Calculated: {total_projects + total_deals}")
