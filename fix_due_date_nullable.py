import os
import sys
from sqlalchemy import text

# Add the project directory to the python path
sys.path.append(os.getcwd())

from app import create_app, db

def fix_schema():
    app = create_app()
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                print("Altering tasks table to make due_date nullable...")
                # MySQL syntax
                connection.execute(text("ALTER TABLE tasks MODIFY COLUMN due_date DATETIME NULL;"))
                connection.commit()
                print("Success: tasks.due_date is now nullable.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    fix_schema()
