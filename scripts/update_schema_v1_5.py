
from config.database import SessionLocal, engine
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_schema():
    db = SessionLocal()
    try:
        # Check if columns exist
        result = db.execute(text("SHOW COLUMNS FROM clients LIKE 'funnel_start_date'"))
        if not result.fetchone():
            logger.info("Adding funnel_start_date column to clients table...")
            db.execute(text("ALTER TABLE clients ADD COLUMN funnel_start_date DATETIME DEFAULT NULL"))
            # Populate existing records with created_at as fallback
            db.execute(text("UPDATE clients SET funnel_start_date = created_at WHERE funnel_start_date IS NULL"))
            logger.info("funnel_start_date column added and populated.")
        else:
            logger.info("funnel_start_date column already exists.")

        result = db.execute(text("SHOW COLUMNS FROM clients LIKE 'status'"))
        if not result.fetchone():
            logger.info("Adding status column to clients table...")
            # Enum: 'lead', 'active_client', 'churned', 'archived' - default to 'lead'
            db.execute(text("ALTER TABLE clients ADD COLUMN status VARCHAR(50) DEFAULT 'lead'"))
            # Update status based on kanban stage or other logic if needed (e.g. if stage is 'won', set to active_client)
            # For now, default all to lead, user can update. 
            # Ideally we check against known 'Won' stages but names vary per company.
            logger.info("status column added.")
        else:
            logger.info("status column already exists.")
            
        db.commit()
        logger.info("Schema update completed successfully.")
        
    except Exception as e:
        logger.error(f"Error updating schema: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting schema update for v1.5...")
    update_schema()
