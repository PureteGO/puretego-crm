import sys
import os
from datetime import datetime
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import db_session, engine, Base
from app.models.company import Company
from app.models.client import Client
from app.models.deal import Deal, DealStatus
from app.models.kanban_stage import KanbanStage

def migrate_sales():
    print("--- Starting Day 2 Sales Migration ---")
    
    # 1. Update Schema
    print("Syncing schema (Creating deals table)...")
    Base.metadata.create_all(bind=engine)
    
    session = db_session
    
    try:
        # 2. Check for missing columns (Schema Migration)
        print("Checking for missing columns...")
        with engine.connect() as conn:
            # Check 'interactions' table for 'deal_id'
            result = conn.execute(text("SHOW COLUMNS FROM interactions LIKE 'deal_id'"))
            if not result.fetchone():
                print("Adding 'deal_id' column to interactions...")
                conn.execute(text("ALTER TABLE interactions ADD COLUMN deal_id INTEGER NULL"))
                conn.execute(text("CREATE INDEX ix_interactions_deal_id ON interactions (deal_id)"))
            
            conn.commit()
            
        # 3. Migrate Clients in Kanban Stages to Deals
        # Strategy: If a client has a kanban_stage_id, create a Deal for them
        print("Migrating existing Leads to Deals...")
        
        clients_with_stage = session.query(Client).filter(Client.kanban_stage_id != None).all()
        deals_created = 0
        
        for client in clients_with_stage:
            # Check if deal already exists for this client to avoid duplicates in multiple runs
            existing_deal = session.query(Deal).filter_by(client_id=client.id).first()
            
            if not existing_deal:
                if not client.company_id:
                    print(f"Skipping client {client.name} (No Company ID)")
                    continue
                    
                print(f"Creating Deal for Client: {client.name}")
                
                # Determine status based on stage name (heuristic)
                stage = session.query(KanbanStage).get(client.kanban_stage_id)
                status = DealStatus.OPEN
                probability = 50
                
                if stage:
                    stage_name = stage.name.lower()
                    if 'ganho' in stage_name or 'fechado' in stage_name or 'won' in stage_name:
                        status = DealStatus.WON
                        probability = 100
                    elif 'perdido' in stage_name or 'lost' in stage_name:
                        status = DealStatus.LOST
                        probability = 0
                
                new_deal = Deal(
                    title=f"Oportunidade {client.name}",
                    company_id=client.company_id,
                    client_id=client.id,
                    owner_id=client.owner_id,
                    kanban_stage_id=client.kanban_stage_id,
                    value=0.0 # Default value
                )
                new_deal.status = status
                new_deal.probability = probability
                
                session.add(new_deal)
                deals_created += 1
        
        session.commit()
        print(f"Migration Complete. Created {deals_created} deals from existing leads.")
        
    except Exception as e:
        session.rollback()
        print(f"CRITICAL ERROR: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate_sales()
