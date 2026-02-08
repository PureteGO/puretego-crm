
import sys
import os
import json
from datetime import datetime, date
from decimal import Decimal

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import Client, Visit, HealthCheck, Proposal, Interaction, ServicePackage, KanbanStage
from config.database import get_db

app = create_app()

def custom_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def export_client(client_name_query):
    with app.app_context():
        with get_db() as db:
            client = db.query(Client).filter(Client.name.like(f"%{client_name_query}%")).first()
            
            if not client:
                print(f"ERROR: Client matching '{client_name_query}' not found.")
                return

            print(f"Found client: {client.name} (ID: {client.id})")
            
            # Serialize Client
            client_data = {
                'name': client.name,
                'gmb_profile_name': client.gmb_profile_name,
                'contact_name': client.contact_name,
                'phone': client.phone,
                'email': client.email,
                'address': client.address,
                'kanban_stage_name': client.kanban_stage.name if client.kanban_stage else None,
                'interested_package_name': client.interested_package.name if client.interested_package else None,
                'created_at': client.created_at
            }
            
            # Serialize Related Data
            # Serialize Related Data
            # Visits
            visits = []
            if getattr(client, 'visits', None):
                for v in client.visits:
                    visits.append({
                        'visit_date': v.visit_date.isoformat() if v.visit_date else None,
                        'notes': v.notes,
                        'next_step': v.next_step,
                        # 'is_completed' not in Visit model
                        # 'location' not in Visit model
                    })
                
            # Health Checks
            health_checks = []
            if getattr(client, 'health_checks', None):
                for h in client.health_checks:
                    health_checks.append({
                        # Model has 'score' and 'report_data' (JSON)
                        'score': h.score,
                        'report_data': h.report_data,
                        'created_at': h.created_at.isoformat() if h.created_at else None
                    })
                
            # Proposals
            proposals = []
            # Check if proposals relationship exists
            if getattr(client, 'proposals', None):
                for p in client.proposals:
                    items_data = []
                    if getattr(p, 'items', None):
                        for item in p.items:
                             # We need the service name to map it on import
                            service_name = item.service.name if item.service else "Unknown Service"
                            items_data.append({
                                'service_name': service_name,
                                'price': float(item.price),
                                'description': item.description
                            })

                    proposals.append({
                        'status': p.status,
                        'total_amount': float(p.total_amount) if p.total_amount else 0.0,
                        'payment_terms': p.payment_terms,
                        'pdf_file_path': p.pdf_file_path,
                        'created_at': p.created_at.isoformat() if p.created_at else None,
                        'items': items_data
                    })
                
            export_data = {
                'client': client_data,
                'visits': visits,
                'health_checks': health_checks,
                'proposals': proposals
            }
            
            # Save to file
            filename = f"export_{client.name.replace(' ', '_')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, default=custom_serializer, indent=2)
                
            print(f"SUCCESS: Data exported to {filename}")
            print("To import this on production, I will create a corresponding import script.")

if __name__ == "__main__":
    export_client("Todo Blanco")
