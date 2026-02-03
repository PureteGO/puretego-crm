from app import create_app
from config.settings import ProductionConfig

# Application Entry Point for cPanel via Passenger
# Last Updated: 2026-02-02
application = create_app(ProductionConfig)
