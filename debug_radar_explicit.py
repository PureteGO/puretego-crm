from app import create_app
from config.database import get_db
from app.models.local_search import LocalScanResult, LocalSearchKeyword, LocalMetricsAggregated
from datetime import datetime
from sqlalchemy import func

app = create_app()

with app.app_context():
    print("--- Debugging Radar Chart Data ---")
    client_id = 1
    today = datetime.now().date()
    # today = datetime(2025, 2, 7).date() # Uncomment to test specific date if needed

    with get_db() as db:
        print(f"Checking data for Client {client_id} on {today}")
        
        # 1. Check Metrics Aggregated
        agg = db.query(LocalMetricsAggregated).filter(
            LocalMetricsAggregated.client_id == client_id,
            func.date(LocalMetricsAggregated.scan_date) == today
        ).first()
        
        if agg:
            print(f"AGGREGATED METRICS FOUND:")
            print(f"  Visibility: {agg.visibility_score}")
            print(f"  Position Score: {agg.avg_position_score}")
            print(f"  Reviews Score: {agg.reviews_score}")
            print(f"  Authority Score: {agg.local_authority_score}")
        else:
            print("NO AGGREGATED METRICS FOUND FOR TODAY.")

        # 2. Check Raw Scan Results for Client
        results = db.query(LocalScanResult).join(LocalSearchKeyword).filter(
            LocalSearchKeyword.client_id == client_id,
            func.date(LocalScanResult.scan_date) == today,
            LocalScanResult.is_client == True
        ).all()
        
        print(f"\nRAW CLIENT RESULTS ({len(results)} found):")
        for r in results:
            print(f"  ID: {r.id} | KW: {r.search_keyword.keyword}")
            print(f"    Position: {r.position} (Type: {type(r.position)})")
            print(f"    Rating: {r.rating} (Type: {type(r.rating)})")
            print(f"    Reviews: {r.reviews} (Type: {type(r.reviews)})")
            print(f"    Place ID: {r.place_id}")
            print("-" * 30)

        # 3. Check Competitors (to see if market avg logic works)
        comp_results = db.query(LocalScanResult).join(LocalSearchKeyword).filter(
            LocalSearchKeyword.client_id == client_id,
            func.date(LocalScanResult.scan_date) == today,
            LocalScanResult.is_client == False
        ).limit(5).all()
        
        print(f"\nSAMPLE COMPETITOR RESULTS ({len(comp_results)} shown):")
        for r in comp_results:
             print(f"  Pos: {r.position}, Rating: {r.rating}, Reviews: {r.reviews}")

