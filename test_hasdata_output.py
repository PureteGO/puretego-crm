from app.services.hasdata_service import HasDataService
import json

def test_hasdata():
    hd = HasDataService()
    # CESS Centro Educativo San Sebastian placeId
    place_id = "ChIJV9zM3mOfYpQR_WJv_8t_Y5E"
    
    print("Testing HasData Place Details...")
    details = hd.get_place_details(place_id)
    with open("hasdata_details.json", "w") as f:
        json.dump(details, f, indent=2)
    print("Details saved to hasdata_details.json")
    
    print("\nTesting HasData Reviews...")
    reviews = hd.get_reviews(place_id)
    with open("hasdata_reviews.json", "w") as f:
        json.dump(reviews, f, indent=2)
    print("Reviews saved to hasdata_reviews.json")

    print("\nTesting HasData Photos...")
    photos = hd.get_photos(place_id)
    with open("hasdata_photos.json", "w") as f:
        json.dump(photos, f, indent=2)
    print("Photos saved to hasdata_photos.json")

if __name__ == "__main__":
    from flask import Flask
    app = Flask(__name__)
    app.config['HASDATA_API_KEY'] = os.environ.get('HASDATA_API_KEY') or ''
    with app.app_context():
        test_hasdata()
