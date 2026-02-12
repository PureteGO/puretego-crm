import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from app import create_app
from app.models import Client
from config.database import db_session
from app.models.local_search import LocalSearchKeyword, LocalScanResult, LocalMetricsAggregated
from app.services.rank_tracker_service import RankTrackerService
from app.services.health_check_service import HealthCheckService

def verify_implementation():
    app = create_app()
    with app.app_context():
        print("1. Creating database tables...")
        # create_app calls init_db(), so tables should be created.
        
        # Verify tables exist (by checking if we can query them)
        try:
            db_session.query(LocalSearchKeyword).first()
            print("   SUCCESS: LocalSearchKeyword table access verified.")
        except Exception as e:
            print(f"   ERROR: LocalSearchKeyword table issues: {e}")
            return

        print("\n2. Verifying RankTrackerService instantiation...")
        try:
            tracker = RankTrackerService()
            print("   SUCCESS: RankTrackerService instantiated.")
        except Exception as e:
            print(f"   ERROR: RankTrackerService instantiation failed: {e}")
            return

        print("\n3. Verifying metric calculation logic (Mock Data)...")
        
        # Get a valid client
        client = db_session.query(Client).first()
        created_client = None
        if not client:
            print("   INFO: No clients found, creating dummy client...")
            created_client = Client(name="Test Client Verify", email="testverify@example.com")
            db_session.add(created_client)
            db_session.commit()
            client_id = created_client.id
        else:
            client_id = client.id
            print(f"   INFO: Using existing Client ID: {client_id}")
        
        scan_date = datetime.now().date()
        
        # Create mock scan results
        mock_keyword = LocalSearchKeyword(client_id=client_id, keyword="test kw", location="test loc")
        db_session.add(mock_keyword)
        db_session.flush()
        
        mock_result = LocalScanResult(
            search_keyword_id=mock_keyword.id,
            scan_date=scan_date,
            position=1,
            reviews=100,
            rating=5.0,
            is_client=True
        )
        db_session.add(mock_result)
        db_session.commit()
        
        # Calculate
        try:
            RankTrackerService.calculate_metrics(client_id, scan_date)
        except Exception as e:
            # It might fail due to detached instance on return, or other things
            # But let's check if the record was created
            print(f"   Note: Method returned, checking DB... ({e})")

        # Verify in DB
        agg = db_session.query(LocalMetricsAggregated).filter_by(client_id=client_id, scan_date=scan_date).first()
        
        if agg:
            print(f"   SUCCESS: Metrics record found in DB. Visibility: {agg.visibility_score}, Pos: {agg.avg_position_score}")
        else:
            print("   ERROR: Metrics record NOT found in DB.")

        # Cleanup
        db_session.delete(mock_result)
        db_session.delete(mock_keyword)
        if agg: db_session.delete(agg)
        db_session.commit()
        print("\nVerification Complete!")

if __name__ == "__main__":
    verify_implementation()
