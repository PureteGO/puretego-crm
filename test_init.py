import traceback
from config.settings import DevelopmentConfig
from app import create_app
try:
    application = create_app(DevelopmentConfig)
    print("SUCCESS")
except Exception as e:
    print("FAILED")
    traceback.print_exc()
