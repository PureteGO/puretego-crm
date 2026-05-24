
import os
import sys
from dotenv import load_dotenv

# Add app directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.gemini_service import GeminiService
from flask import Flask

# Minimal Flask app for context
app = Flask(__name__)
app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

def test_generate_reply():
    print("Testing Gemini review reply generation...")
    
    with app.app_context():
        gemini = GeminiService()
        
        # Test Case 1: Positive review
        print("\nCase 1: Positive review (5 stars)")
        reply1 = gemini.generate_review_reply(
            business_name="PureteGO Spa",
            reviewer_name="Maria Silva",
            rating=5,
            comment="Excelente atendimento e ambiente maravilhoso!",
            language='pt'
        )
        print(f"Reply: {reply1}")
        
        # Test Case 2: Negative review
        print("\nCase 2: Negative review (2 stars)")
        reply2 = gemini.generate_review_reply(
            business_name="PureteGO Spa",
            reviewer_name="João Souza",
            rating=2,
            comment="Achei o preço muito alto pelo serviço oferecido.",
            language='pt'
        )
        print(f"Reply: {reply2}")

if __name__ == "__main__":
    test_generate_reply()
