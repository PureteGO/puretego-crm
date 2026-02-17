
import sys
import os
from flask import Flask

# Add project root to path
sys.path.append(os.getcwd())

from config.settings import config
# Mock get_db before importing service to avoid database connection issues
from unittest.mock import MagicMock
import app.services.health_check_service

mock_db = MagicMock()
app.services.health_check_service.get_db = MagicMock(return_value=mock_db)
mock_db.__enter__.return_value = mock_db

from app.services.health_check_service import HealthCheckService

app = Flask(__name__)
# Load config but be lenient
try:
    app.config.from_object(config['default'])
except:
    app.config['SERPAPI_KEY'] = os.environ.get('SERPAPI_KEY') or ''
    app.config['SERPER_API_KEY'] = os.environ.get('SERPER_API_KEY') or ''

# Mock SerperService to return the same data we saw in debug_serpapi_tool if possible, 
# OR let it run real requests if keys are present.
# The user's env has keys in config probably.

with app.app_context():
    print("Testing HealthCheckService.perform_public_audit...")
    # Use the business name that was giving issues
    business_name = "CESS Centro Educativo San Sebastian"
    
    try:
        result = HealthCheckService.perform_public_audit(None, business_name)
        
        if result['success']:
            print(f"\nFinal Score: {result['score']}/100")
            print("-" * 30)
            for res in result['report']['criteria_results']:
                status = "PASS" if res['passed'] else "FAIL"
                print(f"[{status}] ID {res['id']}: {res['name_es']}")
                
            print("\nRecommendations:")
            for rec in result['report']['recommendations']:
                print(f" - {rec}")
        else:
            print(f"Failed: {result.get('error')}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
