from app import create_app
from app.models import Project, Deal, Client
from config.database import get_db
from sqlalchemy import func
from datetime import datetime

app = create_app()

with app.app_context():
    with get_db() as db:
        first_day_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        print(f"DEBUG: Checking records from: {first_day_month}")

        # 1. Projects
        projects = db.query(Project).filter(
            Project.status != 'cancelled'
        ).all()
        
        print("\n--- ALL PROJECTS (Ordered by Created At) ---")
        for p in projects:
            print(f"ID: {p.id} | Name: {p.name} | Client: {p.client.name} | Setup: {p.total_amount} | Monthly: {p.monthly_value} | Created: {p.created_at}")

        # 2. Deals
        deals = db.query(Deal).filter(
            Deal.status == 'won'
        ).all()
        
        print("\n--- ALL WON DEALS ---")
        for d in deals:
            # Check if has project
            has_project = db.query(Project).filter(Project.deal_id == d.id).first() is not None
            print(f"ID: {d.id} | Title: {d.title} | Client: {d.client.name} | Value: {d.value} | Updated: {d.updated_at} | Has Project: {has_project}")

        # 3. Simulate Dashboard Logic
        projects_val = db.query(
            func.sum(func.coalesce(Project.total_amount, 0))
        ).filter(
            Project.status != 'cancelled',
            Project.created_at >= first_day_month
        ).scalar() or 0
        
        deals_val = db.query(func.sum(Deal.value)).filter(
            Deal.status == 'won',
            Deal.updated_at >= first_day_month,
            ~Deal.id.in_(db.query(Project.deal_id).filter(Project.deal_id != None))
        ).scalar() or 0
        
        print(f"\n--- DASHBOARD CALCULATION (FOR THIS MONTH) ---")
        print(f"Projects Sum: {projects_val}")
        print(f"Deals Sum: {deals_val}")
        print(f"TOTAL: {float(projects_val) + float(deals_val)}")
