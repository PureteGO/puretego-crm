
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
            import json
            import sys
            # Ensure UTF-8 output for windows terminal
            if sys.stdout.encoding != 'utf-8':
                import io
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

            print("SCORE:", result.get('score'))
            if 'report' in result and 'criteria_results' in result['report']:
                failed = [c['name_es'] for c in result['report']['criteria_results'] if not c['passed']]
                print("FAILED CRITERIA:", failed)
            
            # Print full result to file for archive
            with open('final_diagnostic_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("ERROR running health check:")
            print(e)
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_quick_check()
