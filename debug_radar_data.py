from app import create_app
from config.database import db_session
from app.models import Client
from app.models.local_search import LocalSearchKeyword, LocalScanResult, LocalMetricsAggregated
from datetime import datetime

app = create_app()
with app.app_context():
    # Get the client (Assuming ID 1 based on previous context, or list all)
    client_id = 1 
    client = db_session.query(Client).get(client_id)
    print(f"--- Debugging Data for Client: {client.name} (ID: {client_id}) ---")
    
    # Check Keywords
    keywords = db_session.query(LocalSearchKeyword).filter_by(client_id=client_id).all()
    print(f"Keywords: {[k.keyword for k in keywords]}")
    
    # Check Scan Results for today
    today = datetime.now().date()
    results = db_session.query(LocalScanResult).join(LocalSearchKeyword).filter(
        LocalSearchKeyword.client_id == client_id #, LocalScanResult.scan_date >= today
    ).all()
    print(f"Total Scan Results Stored: {len(results)}")
    
    client_results = [r for r in results if r.is_client]
    print(f"Results matching Client: {len(client_results)}")
    for r in client_results:
        print(f" - Found in: {r.keyword_obj.keyword} | Pos: {r.position} | Rating: {r.rating}")
        
    # Check Aggregated Metrics
    agg = db_session.query(LocalMetricsAggregated).filter_by(client_id=client_id).order_by(LocalMetricsAggregated.scan_date.desc()).first()
    if agg:
        print(f"Latest Aggregated Metrics ({agg.scan_date}):")
        print(f" - Visibility: {agg.visibility_score}")
        print(f" - Position: {agg.avg_position_score}")
        print(f" - Reviews: {agg.reviews_score}")
        print(f" - Authority: {agg.local_authority_score}")
    else:
        print("No Aggregated Metrics found.")
        
    print("------------------------------------------------")
