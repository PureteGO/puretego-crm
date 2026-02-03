
import sys
import os

# Add current directory to path just like passenger does
sys.path.append(os.getcwd())

print("Attempting to import application from passenger_wsgi...")

try:
    from passenger_wsgi import application
    print("SUCCESS: 'application' object imported successfully!")
    print(f"App Object: {application}")
except Exception as e:
    print("\n!!! ERROR STARTING APP !!!\n")
    import traceback
    traceback.print_exc()
