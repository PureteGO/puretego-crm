import sys
import os
from sqlalchemy import func
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app
from config.database import db_session
from app.models import Project, Deal

def debug_dashboard():
    app = create_app()
    with app.app_context():
        print("--- Debugging Dashboard Calculations ---")
        
        # Simulate the Dashboard logic
        first_day_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        print(f"Filter Date: {first_day_month}")

        # 1. Projects
        print("\n--- Projects Contributing to Sales (ALL TENANTS) ---")
        projects_query = db_session.query(Project).filter(
            Project.created_at >= first_day_month
        )
        
        projects = projects_query.all()
        total_projects_val = 0
        for p in projects:
            val = (p.total_amount or 0) + (p.monthly_value or 0)
            
            # Check if status is cancelled (which we exclude in dashboard)
            is_excluded = p.status == 'cancelled'
            extra_info = " [EXCLUDED (Cancelled)]" if is_excluded else ""
            
            if not is_excluded:
                total_projects_val += val
            
            print(f"ID: {p.id} | Name: {p.name} | Status: {p.status} | Value: {val} | CompanyID: {p.company_id}{extra_info}")

        print(f"Total Projects Value (Active): {total_projects_val}")

        # 2. Deals
        print("\n--- Deals Contributing to Sales (ALL TENANTS) ---")
        deals_query = db_session.query(Deal).filter(
            Deal.status == 'won',
            Deal.updated_at >= first_day_month,
            ~Deal.id.in_(db_session.query(Project.deal_id).filter(Project.deal_id != None))
        )
        
        deals = deals_query.all()
        total_deals_val = 0
        for d in deals:
            val = d.value or 0
            total_deals_val += val
            print(f"ID: {d.id} | Name: {d.title} | Status: {d.status} | Value: {val} | CompanyID: {d.company_id}")

        print(f"Total Deals Value: {total_deals_val}")
        
        print(f"\nGRAND TOTAL: {total_projects_val + total_deals_val}")

if __name__ == "__main__":
    debug_dashboard()
