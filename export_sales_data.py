import json
from app import create_app
from app.models import Project, Deal, Client
from config.database import get_db

app = create_app()

with app.app_context():
    with get_db() as db:
        data = {
            "projects": [],
            "deals": []
        }
        
        projects = db.query(Project).all()
        for p in projects:
            data["projects"].append({
                "id": p.id,
                "name": p.name,
                "client": p.client.name,
                "total_amount": float(p.total_amount or 0),
                "monthly_value": float(p.monthly_value or 0),
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "deal_id": p.deal_id
            })
            
        deals = db.query(Deal).filter(Deal.status == 'won').all()
        for d in deals:
            # Check if has project
            has_project = db.query(Project).filter(Project.deal_id == d.id).first() is not None
            data["deals"].append({
                "id": d.id,
                "title": d.title,
                "client": d.client.name if d.client else "N/A",
                "value": float(d.value or 0),
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
                "has_project": has_project
            })
            
        with open("sales_data_debug.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("Data exported to sales_data_debug.json")
