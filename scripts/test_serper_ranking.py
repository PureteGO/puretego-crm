
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.serper_service import SerperService
from config.database import get_db
from app.models import KeywordRanking, Client, Company
from app import create_app

def test_serper_flow():
    app = create_app()
    with app.app_context():
        print("1. Testing Serper.dev API Connectivity...")
        service = SerperService()
        if not service.api_key:
            print("WARNING: No SERPER_API_KEY found. Skipping API call.")
        else:
            # Test generic search for "pizza"
            print(f"   Using Key: {service.api_key[:5]}...")
            result = service.search_local_pack("pizza", "Asunción")
            
            if 'error' in result:
                print(f"   API ERROR: {result['error']}")
            else:
                print("   API SUCCESS. Keys returned:", list(result.keys()))
                if 'places' in result:
                    print(f"   Found {len(result['places'])} places.")
        
        print("\n2. Testing Database Storage...")
        with get_db() as db:
            # Find a client
            client = db.query(Client).first()
            if not client:
                print("   No client found to attach ranking to.")
                # Create dummy client
                print("   Creating dummy client...")
                client = Client(name="Test Client SEO")
                db.add(client)
                db.commit()
            
            print(f"   Using Client: {client.name} (ID: {client.id})")
            
            # Create Ranking
            ranking = KeywordRanking(
                client_id=client.id,
                keyword="agencia marketing",
                location="Asunción",
                current_position_local=3,
                current_position_organic=12
            )
            db.add(ranking)
            db.commit()
            print(f"   Saved Ranking ID: {ranking.id}")
            
            # Verify retrieval
            saved = db.query(KeywordRanking).get(ranking.id)
            if saved:
                print(f"   Retrieved Ranking: {saved.keyword} - Pos: {saved.current_position_local}")
                
                # Clean up
                db.delete(saved)
                if client.name == "Test Client SEO":
                    db.delete(client)
                db.commit()
                print("   Cleaned up test data.")
            else:
                print("   ERROR: Could not retrieve saved ranking.")

if __name__ == "__main__":
    test_serper_flow()
