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
        projects = db.query(Project).all()
        
        print("\n--- ALL PROJECTS ---")
        for p in projects:
            is_active_month = p.created_at >= first_day_month and p.status != 'cancelled'
            print(f"[{'X' if is_active_month else ' '}] ID: {p.id} | Name: {p.name} | Client: {p.client.name} | Setup: {p.total_amount} | Created: {p.created_at}")

        # 2. Deals
        deals = db.query(Deal).filter(Deal.status == 'won').all()
        
        print("\n--- ALL WON DEALS ---")
        for d in deals:
            # Check if has project
            has_project_q = db.query(Project).filter(Project.deal_id == d.id).first()
            has_project = has_project_q is not None
            is_active_month = d.updated_at >= first_day_month and not has_project
            print(f"[{'X' if is_active_month else ' '}] ID: {d.id} | Title: {d.title} | Client: {d.client.name} | Value: {d.value} | Updated: {d.updated_at} | Has Project: {has_project} (Project ID: {has_project_q.id if has_project else 'N/A'})")

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
