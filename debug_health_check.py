
import sys
import os
from flask import Flask
from config.database import get_db

# Add project root to path
sys.path.append(os.getcwd())

from app.services.health_check_service import HealthCheckService
from app.services.serpapi_service import SerpApiService
from app.services.serper_service import SerperService
from config.settings import config

app = Flask(__name__)
app.config.from_object(config)

def test_quick_check():
    query = "CESS Centro Educativo San Sebastian"
    print(f"Testing Quick Health Check for: {query}")
    
    with app.app_context():
        try:
            # Check API Keys first
            print(f"SerpApi Key: {'***' if config.SERPAPI_KEY else 'MISSING'}")
            print(f"Serper Key: {'***' if config.SERPER_API_KEY else 'MISSING'}")
            
            # Run service
            result = HealthCheckService.perform_public_audit(None, query)
            print("Result:", result)
        except Exception as e:
            print("ERROR running health check:")
            print(e)
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_quick_check()
