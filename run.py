"""
PureteGO CRM - Application Entry Point
"""
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from dotenv import load_dotenv
    load_dotenv()
    
    from app import create_app
    from config.settings import ProductionConfig, DevelopmentConfig
    
    # Select config based on environment
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        config_class = ProductionConfig
    else:
        config_class = DevelopmentConfig
    
    application = create_app(config_class)
    app = application
    
except Exception as e:
    logger.critical(f"Failed to initialize application: {e}", exc_info=True)
    
    # In production: generic error page, no traceback exposed
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    @application.route('/<path:path>')
    def startup_error(path=None):
        return """
        <html>
            <body style="font-family: sans-serif; padding: 40px; text-align: center;">
                <h1 style="color: #d9534f;">Service Temporarily Unavailable</h1>
                <p>The application failed to start. Our team has been notified.</p>
                <p>Please try again in a few minutes.</p>
            </body>
        </html>
        """, 503
    app = application

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000, debug=(os.environ.get('FLASK_ENV') != 'production'))
