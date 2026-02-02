import sys
import os

print(f"Python executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")

try:
    print("Attempting to import Flask...")
    import flask
    print(f"Flask version: {flask.__version__}")
    
    print("Attempting to import app...")
    sys.path.insert(0, os.getcwd())
    from app import create_app
    print("Import successful. Creating app...")
    
    app = create_app()
    print("App created successfully.")
    
except Exception as e:
    print("ERROR CAUGHT:")
    import traceback
    traceback.print_exc()
