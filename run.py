import sys
import os
from dotenv import load_dotenv

# Ensure the app directory is in the path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
load_dotenv()

from app import create_app
from config.settings import ProductionConfig

# Create the application object for Passenger
# Passenger looks for a variable named 'application' by default
application = create_app(ProductionConfig)
app = application # Fallback for entry point 'app'

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000)
