import sys
import os
import json
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import create_app
from config.database import get_db
from app.models import Client, Deal, DealStatus, KanbanStage, User

def run_endpoint_tests():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for easier endpoint testing
    
    client_app = app.test_client()
    
    with app.app_context():
        with get_db() as db:
            print("--- Running Kanban HTTP Endpoint Tests ---")
            
            # 1. Fetch a valid user from the database to log in
            user = db.query(User).first()
            if not user:
                print("No user found in DB. Creating dummy User...")
                user = User(name="Test User", email="test_endpoint@example.com", password="password123", company_id=1)
                db.add(user)
                db.flush()
            
            # Fetch a stage or create one
            stage = db.query(KanbanStage).filter(KanbanStage.company_id == user.company_id).first()
            if not stage:
                print("Creating dummy KanbanStage...")
                stage = KanbanStage(name="Etapa Teste Endpoints", company_id=user.company_id, order=1)
                db.add(stage)
                db.flush()
                
            # Create a test client and deal
            test_client = Client(
                name="Cliente Teste Endpoints",
                company_id=user.company_id,
                owner_id=user.id,
                kanban_stage_id=stage.id
            )
            db.add(test_client)
            db.flush()
            
            test_deal = Deal(
                title="Negocio Teste Endpoints",
                company_id=user.company_id,
                client_id=test_client.id,
                owner_id=user.id,
                kanban_stage_id=stage.id,
                value=1200000.0
            )
            db.add(test_deal)
            db.commit()
            
            print(f"Entities created. Client: {test_client.id}, Deal: {test_deal.id}")
            
            # Store IDs to reference in request urls
            client_id = test_client.id
            deal_id = test_deal.id
            user_id = user.id
            company_id = user.company_id
            
        # Log in the user using Flask session
        with client_app.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['company_id'] = company_id
            sess['role'] = 'owner'
            sess['permissions'] = {}
        
        # Test 1: GET /clients/kanban
        print("Testing: GET /clients/kanban")
        res = client_app.get('/clients/kanban')
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert b"Pipeline" in res.data or b"Vendas" in res.data or b"Sales" in res.data, "Kanban page should render successfully"
        
        # Test 2: POST /clients/<id>/remove-from-kanban (Manual Removal)
        print(f"Testing: POST /clients/{client_id}/remove-from-kanban")
        res = client_app.post(f'/clients/{client_id}/remove-from-kanban')
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = json.loads(res.data)
        assert data['success'] is True, "Should succeed removing client"
        
        # Test 3: POST /clients/kanban/deals/<id>/remove (Manual Removal)
        print(f"Testing: POST /clients/kanban/deals/{deal_id}/remove")
        res = client_app.post(f'/clients/kanban/deals/{deal_id}/remove')
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = json.loads(res.data)
        assert data['success'] is True, "Should succeed removing deal"
        
        # Test 4: GET /clients/kanban/removed (Removed Repository)
        print("Testing: GET /clients/kanban/removed")
        res = client_app.get('/clients/kanban/removed')
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert b"Cliente Teste Endpoints" in res.data, "Removed repository should list the removed client"
        assert b"Negocio Teste Endpoints" in res.data, "Removed repository should list the removed deal"
        
        # Test 5: POST /clients/<id>/restore-to-kanban (Restoration)
        print(f"Testing: POST /clients/{client_id}/restore-to-kanban")
        res = client_app.post(f'/clients/{client_id}/restore-to-kanban')
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = json.loads(res.data)
        assert data['success'] is True, "Should succeed restoring client"
        
        # Test 6: POST /clients/kanban/deals/<id>/restore (Restoration)
        print(f"Testing: POST /clients/kanban/deals/{deal_id}/restore")
        res = client_app.post(f'/clients/kanban/deals/{deal_id}/restore')
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = json.loads(res.data)
        assert data['success'] is True, "Should succeed restoring deal"
        
        # 3. Verify in DB they are restored, and cleanup
        with app.app_context():
            with get_db() as db:
                c = db.query(Client).get(client_id)
                d = db.query(Deal).get(deal_id)
                
                assert c.status == "lead", "Client status should be restored to lead"
                assert d.status == DealStatus.OPEN, "Deal status should be restored to OPEN"
                
                # Cleanup
                db.delete(d)
                db.delete(c)
                db.commit()
                print("Database entities cleaned up successfully.")
                
        print("--- All Endpoint tests passed successfully! ---")

if __name__ == '__main__':
    run_endpoint_tests()
