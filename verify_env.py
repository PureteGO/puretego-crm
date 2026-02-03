
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

print("--- DIAGNOSTIC START ---")
print(f"CWD: {os.getcwd()}")
print(f"Python: {sys.version}")

try:
    from app import create_app
    print("1. [OK] App Factory Import")
except Exception as e:
    print(f"1. [FAIL] App Factory Import: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.services import SerpApiService
    print("2. [OK] SerpApi Service Import")
except Exception as e:
    print(f"2. [FAIL] SerpApi Service Import: {e}")
    import traceback
    traceback.print_exc()

try:
    app = create_app()
    with app.app_context():
        from config.database import get_db
        with get_db() as db:
            print("3. [OK] DB Connection")
except Exception as e:
    print(f"3. [FAIL] DB Connection: {e}")
    import traceback
    traceback.print_exc()

print("--- DIAGNOSTIC END ---")
