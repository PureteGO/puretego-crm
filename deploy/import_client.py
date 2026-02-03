
import sys
import os
import json
from datetime import datetime

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import Client, Visit, HealthCheck, Proposal, ProposalItem, ServicePackage, KanbanStage, Service
from config.database import get_db, db_session

app = create_app()

# EMBEDDED DATA FROM EXPORT
DATA = {
  "client": {
    "name": "TODO Blanco Uniformes",
    "gmb_profile_name": "Todo Blanco Uniformes",
    "contact_name": "Sra Dalila",
    "phone": "+595 992 435087",
    "email": "",
    "address": "Gaspar R De Francia, San Lorenzo 111423 https://share.google/4uofZ9CjvX6jVaUpG",
    "kanban_stage_name": "Proposta Enviada",
    "interested_package_name": null,
    "created_at": "2026-02-02T22:11:09"
  },
  "visits": [
    {
      "visit_date": "2026-01-28T10:11:00",
      "notes": "Disse que nao havia recebido a proposta eu confirmei que enviei e a Sra Dalila pediu pra secretaria e me disse que iria analizar com a encarregada de redes sociais e me ligaria, nao vou esperar!",
      "next_step": "Visitar amanha ter\u00e7a dia 02/02"
    }
  ],
  "health_checks": [
    {
      "score": 45,
      "report_data": {
        "business_name": "Todo Blanco Uniformes",
        "criteria": [
          { "id": 1, "name_pt": "Hor\u00e1rio de Funcionamento", "score": 6, "status": "positive", "message": "Hor\u00e1rio configurado" },
          { "id": 2, "name_pt": "Fotos dos Produtos/Servi\u00e7os", "score": 0, "status": "critical", "message": "Sem fotos de produtos/servi\u00e7os" },
          { "id": 3, "name_pt": "V\u00eddeos", "score": 0, "status": "critical", "message": "Sem v\u00eddeos" },
          { "id": 4, "name_pt": "Perfil Verificado", "score": 0, "status": "critical", "message": "Perfil n\u00e3o verificado" },
          { "id": 5, "name_pt": "Possui Site", "score": 7, "status": "positive", "message": "Possui website" },
          { "id": 6, "name_pt": "Perguntas e Respostas", "score": 0, "status": "critical", "message": "Sem perguntas e respostas" },
          { "id": 7, "name_pt": "Posts/Publica\u00e7\u00f5es", "score": 0, "status": "critical", "message": "Sem publica\u00e7\u00f5es" },
          { "id": 8, "name_pt": "Descri\u00e7\u00e3o do Neg\u00f3cio", "score": 0, "status": "critical", "message": "Sem descri\u00e7\u00e3o" },
          { "id": 9, "name_pt": "Presen\u00e7a nas Redes Sociais", "score": 0, "status": "critical", "message": "Sem redes sociais" },
          { "id": 10, "name_pt": "Presen\u00e7a no Google Maps", "score": 8, "status": "positive", "message": "Localiza\u00e7\u00e3o no Maps" },
          { "id": 11, "name_pt": "Fotos do Exterior", "score": 0, "status": "critical", "message": "Sem fotos do exterior" },
          { "id": 12, "name_pt": "Fotos do Interior", "score": 0, "status": "critical", "message": "Sem fotos do interior" },
          { "id": 13, "name_pt": "Informa\u00e7\u00f5es de Produtos e Servi\u00e7os", "score": 6, "status": "positive", "message": "Produtos/servi\u00e7os cadastrados" },
          { "id": 14, "name_pt": "Possui Avalia\u00e7\u00f5es", "score": 7, "status": "positive", "message": "157 avalia\u00e7\u00f5es" },
          { "id": 15, "name_pt": "Endere\u00e7o Configurado", "score": 6, "status": "positive", "message": "Endere\u00e7o configurado" },
          { "id": 16, "name_pt": "Possui Logotipo", "score": 5, "status": "positive", "message": "Possui logotipo" },
          { "id": 17, "name_pt": "Resposta a Avalia\u00e7\u00f5es", "score": 0, "status": "critical", "message": "N\u00e3o responde avalia\u00e7\u00f5es" }
        ],
        "summary": {
          "critical_issues_count": 10,
          "moderate_issues_count": 0,
          "positive_points_count": 7,
          "recommendations": [
            "Perfil GMB necessita de otimiza\u00e7\u00e3o urgente",
            "Prioridade: Sem fotos de produtos/servi\u00e7os",
            "Prioridade: Sem v\u00eddeos",
            "Prioridade: Perfil n\u00e3o verificado"
          ]
        }
      },
      "created_at": "2026-02-02T22:13:37"
    },
    {
      "score": 45,
      "report_data": { 
          "business_name": "Todo Blanco Uniformes",
          "criteria": [], 
          "summary": { "recommendations": ["(Segundo Health Check Resumido for brevity)"] } 
      },
      "created_at": "2026-02-02T22:19:27"
    }
  ],
  "proposals": [
    {
      "status": "draft",
      "total_amount": 3500000.0,
      "payment_terms": "50% a la firma, 50% contra entrega.",
      "pdf_file_path": "", # Reset PDF path as file won't exist on server yet
      "created_at": "2026-02-03T07:37:58",
      "items": [
        {
          "service_name": "Dominaci\u00f3n en Google Maps - Pack 90 d\u00edas",
          "price": 3500000.0,
          "description": "Auditor\u00eda SEO Local avanzada, optimizaci\u00f3n t\u00e9cnica..."
        }
      ]
    }
  ]
}

def import_data():
    with app.app_context():
        print(f"Importing client: {DATA['client']['name']}...")
        
        # 1. Create/Find Client
        existing_client = Client.query.filter_by(name=DATA['client']['name']).first()
        if existing_client:
            print("Client already exists. Skipping creation.")
            client = existing_client
        else:
            # Resolve Kanban Stage
            stage_name = DATA['client']['kanban_stage_name']
            stage = KanbanStage.query.filter_by(name=stage_name).first() if stage_name else None
            
            # Resolve Package
            pkg_name = DATA['client']['interested_package_name']
            pkg = ServicePackage.query.filter_by(name=pkg_name).first() if pkg_name else None
            
            client = Client(
                name=DATA['client']['name'],
                gmb_profile_name=DATA['client']['gmb_profile_name'],
                contact_name=DATA['client']['contact_name'],
                phone=DATA['client']['phone'],
                email=DATA['client']['email'],
                address=DATA['client']['address'],
                kanban_stage_id=stage.id if stage else None,
                interested_package_id=pkg.id if pkg else None
            )
            # Override created_at
            if DATA['client']['created_at']:
                client.created_at = datetime.fromisoformat(DATA['client']['created_at'])
                
            db_session.add(client)
            db_session.flush() # Get ID
            print(f"Created client with ID: {client.id}")

        # 2. Import Visits
        print("Importing visits...")
        for v_data in DATA['visits']:
            # Check if duplicate (simple check by date)
            dt = datetime.fromisoformat(v_data['visit_date'])
            exists = Visit.query.filter_by(client_id=client.id, visit_date=dt).first()
            if not exists:
                visit = Visit(
                    client_id=client.id,
                    user_id=1, # Assign to admin/first user default
                    visit_date=dt,
                    notes=v_data['notes'],
                    next_step=v_data['next_step']
                )
                db_session.add(visit)

        # 3. Import Health Checks
        print("Importing health checks...")
        for h_data in DATA['health_checks']:
            # Simple deduplication could be done here but skipping for simplicity
            hc = HealthCheck(
                client_id=client.id,
                score=h_data['score'],
                report_data=h_data['report_data']
            )
            if h_data['created_at']:
                hc.created_at = datetime.fromisoformat(h_data['created_at'])
            db_session.add(hc)

        # 4. Import Proposals
        print("Importing proposals...")
        for p_data in DATA['proposals']:
            # Check duplicates
            p_dt = datetime.fromisoformat(p_data['created_at'])
            exists = Proposal.query.filter_by(client_id=client.id, created_at=p_dt).first()
            if not exists:
                prop = Proposal(
                    client_id=client.id,
                    user_id=1, # Default Admin
                    total_amount=p_data['total_amount'],
                    payment_terms=p_data['payment_terms'],
                    status=p_data['status']
                )
                prop.pdf_file_path = p_data['pdf_file_path'] # Will be empty or invalid path, but okay
                if p_data['created_at']:
                    prop.created_at = p_dt
                
                db_session.add(prop)
                db_session.flush()
                
                # Import Items
                for item_data in p_data['items']:
                    # Find Service ID
                    srv = Service.query.filter_by(name=item_data['service_name']).first()
                    # Fallback if specific name match fails -> use first service or skip?
                    # The Service table MUST be populated by seed_db.py for this to work.
                    service_id = srv.id if srv else 1 
                    
                    if not srv:
                        print(f"WARNING: Service '{item_data['service_name']}' not found. Defaulting to ID 1.")
                        
                    item = ProposalItem(
                        proposal_id=prop.id,
                        service_id=service_id,
                        price=item_data['price'],
                        description=item_data['description']
                    )
                    db_session.add(item)

        try:
            db_session.commit()
            print("Import completed successfully!")
        except Exception as e:
            db_session.rollback()
            print(f"Error importing client: {e}")
            raise

if __name__ == '__main__':
    import_data()
