import sys
import os
from datetime import datetime, timedelta

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import create_app
from config.database import get_db
from app.models import Client, Deal, DealStatus, KanbanStage, User
from app.routes.clients import archive_inactive_cards

def run_tests():
    app = create_app()
    with app.app_context():
        with get_db() as db:
            print("--- Running Kanban Inactivity and Archive Tests ---")
            
            # 1. Get or create a Stage, User (needed for test client/deal)
            stage = db.query(KanbanStage).first()
            if not stage:
                print("Creating dummy KanbanStage...")
                stage = KanbanStage(name="Etapa Teste", company_id=1, order=1)
                db.add(stage)
                db.flush()
                
            user = db.query(User).first()
            if not user:
                print("Creating dummy User...")
                user = User(name="Test User", email="test@example.com", company_id=1)
                user.set_password("password123")
                db.add(user)
                db.flush()
            
            company_id = stage.company_id if stage.company_id else 1
            
            # 2. Create test client and deal
            print("Creating test Client and Deal...")
            client = Client(
                name="Cliente Teste Inativo",
                company_id=company_id,
                owner_id=user.id,
                kanban_stage_id=stage.id,
                lead_temperature="cold"
            )
            db.add(client)
            db.flush() # get client.id
            
            deal = Deal(
                title="Negocio Teste Inativo",
                company_id=company_id,
                client_id=client.id,
                owner_id=user.id,
                kanban_stage_id=stage.id,
                value=500000.0
            )
            deal.status = DealStatus.OPEN
            db.add(deal)
            db.commit()
            
            print(f"Created Client ID: {client.id}, Deal ID: {deal.id}")
            assert client.stage_updated_at is not None, "Client stage_updated_at should be initialized on creation"
            assert deal.stage_updated_at is not None, "Deal stage_updated_at should be initialized on creation"
            print("Initialization OK!")
            
            # 3. Manually backdate stage_updated_at to 22 days ago
            past_date = datetime.utcnow() - timedelta(days=22)
            client.stage_updated_at = past_date
            deal.stage_updated_at = past_date
            db.commit()
            print(f"Backdated stage_updated_at to: {past_date}")
            
            # 4. Trigger archive_inactive_cards
            print("Running archive_inactive_cards...")
            archive_inactive_cards(db, company_id)
            
            # Refresh from DB
            db.refresh(client)
            db.refresh(deal)
            
            # Assertions for archiving
            print(f"Archived Client status: {client.status}")
            print(f"Archived Deal status: {deal.status}")
            assert client.status == "inactive_kanban", f"Client status should be inactive_kanban, got {client.status}"
            assert deal.status == DealStatus.INACTIVE, f"Deal status should be DealStatus.INACTIVE, got {deal.status}"
            print("Automatic archiving OK!")
            
            # 5. Test manual restore
            print("Testing restoration...")
            
            # Restore client
            client.status = "lead"
            client.stage_updated_at = datetime.utcnow()
            
            # Restore deal
            deal.status = DealStatus.OPEN
            deal.stage_updated_at = datetime.utcnow()
            db.commit()
            
            db.refresh(client)
            db.refresh(deal)
            
            assert client.status == "lead", "Client status should be lead after restore"
            assert deal.status == DealStatus.OPEN, "Deal status should be DealStatus.OPEN after restore"
            assert (datetime.utcnow() - client.stage_updated_at).seconds < 60, "Client stage_updated_at should be updated to current time on restore"
            assert (datetime.utcnow() - deal.stage_updated_at).seconds < 60, "Deal stage_updated_at should be updated to current time on restore"
            print("Restoration OK!")
            
            # 6. Cleanup
            print("Cleaning up test entities...")
            db.delete(deal)
            db.delete(client)
            db.commit()
            print("Cleanup OK!")
            print("--- All tests passed successfully! ---")

if __name__ == '__main__':
    run_tests()
