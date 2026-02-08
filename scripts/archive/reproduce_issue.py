
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.services import SerpApiService
from config.settings import config

def test_serpapi_parsing():
    print("Testing SerpApiService parsing logic...")
    
    # Mock SerpApi response (typical google_maps search)
    mock_response = {
        "local_results": [
            {
                "title": "Kess Beleza Campo Grande MS",
                "place_id": "ChIJuS9n98N...",
                "address": "Av. Afonso Pena, 1234",
                "operating_hours": {"monday": "08:00–18:00"},
                "website": "https://kessbeleza.com",
                "thumbnail": "https://thumbnail.url",
                "photos": ["p1", "p2", "p3", "p4", "p5"],
                "reviews": 15,
                "verified": True
            }
        ]
    }
    
    serp = SerpApiService()
    
    # Test the full parsing flow
    analysis = serp.analyze_gmb_profile("Kess Beleza", location="Campo Grande MS")
    
    # Manually simulate part of the internal logic for the mock to avoid network calls
    # but the script should test the parsing logic I just wrote.
    # Actually, I'll update the script to test the inner _evaluate_criteria with 
    # the extracted business data to be sure.
    
    business_data = mock_response['local_results'][0]
    results = serp._evaluate_criteria(business_data, None)
    total_score = sum(item['score'] for item in results)
    
    print(f"\nResults count: {len(results)}")
    print(f"Total Score: {total_score}")
    
    positive = [r for r in results if r['status'] == 'positive']
    moderate = [r for r in results if r['status'] == 'moderate']
    critical = [r for r in results if r['status'] == 'critical']
    
    print(f"Positive: {len(positive)}")
    print(f"Moderate: {len(moderate)}")
    print(f"Critical: {len(critical)}")
    
    if len(results) != 17:
        print(f"WARNING: Expected 17 criteria, got {len(results)}")

if __name__ == "__main__":
    test_serpapi_parsing()
