import sys
import os
from sqlalchemy import func

# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app
from config.database import db_session
from app.models import Deal

def fix_data():
    app = create_app()
    with app.app_context():
        print("--- Fixing Dashboard Data ---")
        
        # Find the invalid deal
        deal_to_delete = db_session.query(Deal).filter(
            Deal.value == 1500.0,
            Deal.title.like('%Sabor%')
        ).first()
        
        if deal_to_delete:
            print(f"Found Deal: ID={deal_to_delete.id}, Title='{deal_to_delete.title}', Value={deal_to_delete.value}")
            
            # Delete it
            db_session.delete(deal_to_delete)
            db_session.commit()
            print("Deal deleted successfully.")
        else:
            print("Deal not found.")

if __name__ == "__main__":
    fix_data()
