
from app import create_app
from config.database import get_db
from app.models import Project, Deal
from sqlalchemy import func
from datetime import datetime, date

app = create_app()

with app.app_context():
    with get_db() as db:
        today = date.today()
        first_day_month = today.replace(day=1)
        
        print(f"--- Debugging Sales for {first_day_month} to {today} ---")
        
        # 1. Projects Analysis
        print("\n[ACTIVE PROJECTS check]")
        projects = db.query(Project).filter(Project.status == 'active').all()
        
        total_proj_val = 0
        for p in projects:
            start = p.start_date
            created = p.created_at.date() if p.created_at else None
            
            eff_date = start if start else created
            
            in_month = eff_date >= first_day_month
            
            val = (p.total_amount or 0) + (p.monthly_value or 0)
            
            print(f"ID: {p.id} | Name: {p.name} | Status: {p.status} | Deal ID: {p.deal_id}")
            print(f"  Start: {start} | Created: {created} | Eff Date: {eff_date}")
            print(f"  In Current Month? {in_month}")
            print(f"  Value: {val} (Total: {p.total_amount}, Monthly: {p.monthly_value})")
            
            if in_month:
                total_proj_val += val
                print("  -> INCLUDED in New Logic")
            else:
                print("  -> EXCLUDED in New Logic")
                
            # Compare with Old Logic: created >= first_day
            if created and created >= first_day_month:
                print("  -> WOULD BE INCLUDED in Old Logic (Created >= First Day)")
            else:
                print("  -> WOULD BE EXCLUDED in Old Logic")
                
        print(f"\nCalculated Project Value (New Logic): {total_proj_val}")

        # 2. Deals Analysis
        print("\n[WON DEALS check]")
        # Logic: Deals won this month, excluding those that are already projects
        # But wait, existing logic uses Interaction check or just Deal.updated_at?
        # Let's check dashboard.py logic for deals:
        # deals_val = filter_by_company(db.query(func.sum(Deal.value)), Deal).filter(
        #     Deal.status == 'won',
        #     Deal.closed_at >= first_day_month,
        #     ~Deal.id.in_(db.query(Project.deal_id).filter(Project.deal_id.isnot(None))) 
        # ).scalar() or 0
        
        deals = db.query(Deal).filter(
            Deal.status == 'won',
            Deal.closed_at >= first_day_month
        ).all()
        
        total_deal_val = 0
        for d in deals:
            # Check if linked to project
            linked_proj = db.query(Project).filter(Project.deal_id == d.id).first()
            is_excluded = linked_proj is not None
            
            print(f"Deal ID: {d.id} | Name: {d.name} | Val: {d.value} | Closed: {d.closed_at}")
            print(f"  Linked Project? {linked_proj.id if linked_proj else 'No'}")
            
            if not is_excluded:
                total_deal_val += (d.value or 0)
                print("  -> INCLUDED (Won Deal, No Project)")
            else:
                print("  -> EXCLUDED (Has Project)")

        print(f"\nCalculated Deal Value: {total_deal_val}")
        
        print(f"\nGRAND TOTAL (Sales Closed): {total_proj_val + total_deal_val}")
