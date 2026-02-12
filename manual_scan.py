from app import create_app
from app.services.rank_tracker_service import RankTrackerService
import logging

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

app = create_app()
with app.app_context():
    print("--- Starting Manual Scan ---")
    client_id = 1
    
    try:
        result = RankTrackerService.perform_scan(client_id)
        print("Scan Result:", result)
        
        if result.get('success'):
            print("Metrics:", result.get('metrics'))
            # Check DB again
            from app.models.local_search import LocalMetricsAggregated
            from config.database import db_session
            from datetime import datetime
            
            agg = db_session.query(LocalMetricsAggregated).filter_by(
                client_id=client_id, 
                scan_date=datetime.now().date()
            ).first()
            if agg:
                print(f"DB Verification: Found agg with visibility {agg.visibility_score}")
            else:
                print("DB Verification: FAILED to find agg record.")
        else:
            print("Scan Failed:", result.get('error'))
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
