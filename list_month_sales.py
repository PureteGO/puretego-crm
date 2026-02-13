import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app
from config.database import db_session
from app.models import Project, Deal

def list_sales():
    app = create_app()
    with app.app_context():
        first_day_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        print(f"--- Vendas Fechadas (Desde {first_day_month.strftime('%d/%m/%Y')}) ---")
        
        # 1. Projects
        projects = db_session.query(Project).filter(
            Project.created_at >= first_day_month,
            Project.status != 'cancelled'
        ).all()
        
        for p in projects:
            val = (p.total_amount or 0) + (p.monthly_value or 0)
            print(f"PROJETO: {p.name} | Valor: {val:,.2f} Gs | Data: {p.created_at.strftime('%d/%m/%Y')}")

        # 2. Deals
        deals = db_session.query(Deal).filter(
            Deal.status == 'won',
            Deal.updated_at >= first_day_month,
            ~Deal.id.in_(db_session.query(Project.deal_id).filter(Project.deal_id != None))
        ).all()
        
        for d in deals:
            val = d.value or 0
            print(f"OPORTUNIDADE: {d.title} | Valor: {val:,.2f} Gs | Data: {d.updated_at.strftime('%d/%m/%Y')}")

if __name__ == "__main__":
    list_sales()
