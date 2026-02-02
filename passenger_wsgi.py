from app import create_app
from config.settings import ProductionConfig

application = create_app(ProductionConfig)
