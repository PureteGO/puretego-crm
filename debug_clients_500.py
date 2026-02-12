from app import create_app
from config.database import get_db, db_session
from app.models import Client, KanbanStage, User, Role
from flask import session

app = create_app()

with app.test_request_context('/clients/'):
    with app.app_context():
        # Simulate session
        with app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['company_id'] = 1
            sess['company_name'] = 'Test Company'
            sess['role'] = 'owner'
            
        print("--- Testing Clients Index Route ---")
        try:
            from app.routes.clients import index
            # Mocking request args if necessary, technically test_request_context handles basic
            # We can invoke the view function directly since we're in request context
            response = index()
            print("Successfully rendered template or returned response.")
        except Exception as e:
            import traceback
            print("CAUGHT EXCEPTION:")
            traceback.print_exc()
