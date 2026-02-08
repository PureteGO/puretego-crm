import sys
import os

# Add root dir to path
sys.path.append(os.getcwd())

from config.database import engine, Base
from app.models.quick_check_log import QuickCheckLog

print("Creating QuickCheckLog table...")
Base.metadata.create_all(bind=engine)
print("Table created successfully (if it didn't exist).")
