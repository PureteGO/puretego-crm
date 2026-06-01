import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import create_app
from config.database import get_db
from app.models import Client, Deal, KanbanStage, User, Lead, LeadActivity

def run_prospecting_tests():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    client_app = app.test_client()
    
    with app.app_context():
        with get_db() as db:
            print("--- Running Prospecting Leads Tests ---")
            
            # Fetch a valid user from the database to log in
            user = db.query(User).first()
            if not user:
                print("No user found in DB. Creating dummy User...")
                user = User(name="Test User", email="test_prospecting@example.com", password="password123", company_id=1)
                db.add(user)
                db.flush()
                
            user_id = user.id
            company_id = user.company_id
            
        # Log in the user using Flask session
        with client_app.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['company_id'] = company_id
            sess['role'] = 'owner'
            sess['permissions'] = {}

        # 1. Test GET /prospecting/leads (Listing page)
        print("Testing: GET /prospecting/leads")
        res = client_app.get('/prospecting/leads')
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        
        # 2. Test POST /prospecting/leads/create (Manual Lead Creation)
        print("Testing: POST /prospecting/leads/create")
        lead_data = {
            'company_name': 'Empresa de Teste Automático',
            'source': 'field_visit',
            'maps_link': 'https://google.com/maps/place/test',
            'address': 'Rua Teste, 123',
            'city': 'Asunción',
            'neighborhood': 'Villa Morra',
            'qualification': 'hot',
            'business_health': 'Perfil digital fraco no GMB',
            'prospecting_method': 'whatsapp',
            'status': 'new',
            'observations': 'Próximo passo é ligar'
        }
        res = client_app.post('/prospecting/leads/create', data=lead_data)
        assert res.status_code == 302, f"Expected 302 redirect after creation, got {res.status_code}"
        
        # Verify in DB
        with get_db() as db:
            lead = db.query(Lead).filter(Lead.company_name == 'Empresa de Teste Automático', Lead.company_id == company_id).first()
            assert lead is not None, "Lead was not saved to database"
            assert lead.city == 'Asunción'
            assert lead.neighborhood == 'Villa Morra'
            assert lead.qualification == 'hot'
            assert lead.status == 'new'
            
            # Verify activity is registered
            activity = db.query(LeadActivity).filter(LeadActivity.lead_id == lead.id).first()
            assert activity is not None, "Lead creation activity was not logged"
            assert activity.action == 'created'
            
            lead_id = lead.id
            print(f"Created Lead ID: {lead_id}")
            
        # 3. Test GET /prospecting/leads/<id> (View Lead)
        print(f"Testing: GET /prospecting/leads/{lead_id}")
        res = client_app.get(f'/prospecting/leads/{lead_id}')
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert b"Empresa de Teste" in res.data, "Should display lead company name"
        
        # 4. Test POST /prospecting/leads/<id>/edit (Edit Lead)
        print(f"Testing: POST /prospecting/leads/{lead_id}/edit")
        edit_data = lead_data.copy()
        edit_data['company_name'] = 'Empresa de Teste Editada'
        edit_data['status'] = 'contacting'
        res = client_app.post(f'/prospecting/leads/{lead_id}/edit', data=edit_data)
        assert res.status_code == 302, f"Expected 302, got {res.status_code}"
        
        # Verify in DB
        with get_db() as db:
            lead = db.query(Lead).get(lead_id)
            assert lead.company_name == 'Empresa de Teste Editada'
            assert lead.status == 'contacting'
            
            # Verify status change activity is registered
            status_activity = db.query(LeadActivity).filter(
                LeadActivity.lead_id == lead_id, 
                LeadActivity.action == 'status_change'
            ).first()
            assert status_activity is not None, "Status change activity was not logged"
            
        # 5. Test POST /prospecting/leads/<id>/activity (Log Activity Note)
        print(f"Testing: POST /prospecting/leads/{lead_id}/activity")
        res = client_app.post(f'/prospecting/leads/{lead_id}/activity', data={
            'notes': 'Ligação feita, agendado visita.',
            'action': 'note_added'
        })
        assert res.status_code == 302, f"Expected 302, got {res.status_code}"
        
        # Verify activity in DB
        with get_db() as db:
            note_act = db.query(LeadActivity).filter(
                LeadActivity.lead_id == lead_id,
                LeadActivity.notes == 'Ligação feita, agendado visita.'
            ).first()
            assert note_act is not None, "Custom note activity was not logged"
            
        # 6. Test POST /prospecting/leads/<id>/convert (Convert Lead)
        print(f"Testing: POST /prospecting/leads/{lead_id}/convert")
        res = client_app.post(f'/prospecting/leads/{lead_id}/convert')
        assert res.status_code == 302, f"Expected 302 redirect after conversion, got {res.status_code}"
        
        # Verify conversion results in DB
        with get_db() as db:
            lead = db.query(Lead).get(lead_id)
            assert lead.status == 'converted', "Lead status should be converted"
            
            # Fetch the newly created client
            client = db.query(Client).filter(Client.name == 'Empresa de Teste Editada', Client.company_id == company_id).first()
            assert client is not None, "Client was not created"
            assert client.status == 'lead', "Client status in Kanban pipeline should be 'lead'"
            assert 'Villa Morra, Asunción' in client.address, "Client address should contain neighborhood and city"
            
            # Fetch deal
            deal = db.query(Deal).filter(Deal.client_id == client.id).first()
            assert deal is not None, "Deal was not created"
            assert deal.title == f"Oportunidade {client.name}"
            
            # Cleanup created test entities
            db.delete(deal)
            
            # If a GMBLocationLink was created, delete it
            from app.models.gmb_location_link import GMBLocationLink
            gmb_link = db.query(GMBLocationLink).filter(GMBLocationLink.client_id == client.id).first()
            if gmb_link:
                db.delete(gmb_link)
                
            db.delete(client)
            db.delete(lead) # Will cascade delete lead activities
            db.commit()
            
            print("Database cleaned up successfully.")
            
        print("--- All Prospecting Leads Tests Passed Successfully! ---")

if __name__ == '__main__':
    run_prospecting_tests()
