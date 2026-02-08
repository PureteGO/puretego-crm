
import sys
import os

# Ensure we can import from the app root
sys.path.append(os.getcwd())

from config import init_db
from app import create_app

# Create app context to ensure config is loaded
app = create_app()
with app.app_context():
    print("Initializing database tables via SQLAlchemy Base.metadata.create_all()...")
    init_db()
    print("Database tables created successfully!")
