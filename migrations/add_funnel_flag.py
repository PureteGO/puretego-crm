from config.database import engine
from sqlalchemy import text

def upgrade():
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("SHOW COLUMNS FROM kanban_stages LIKE 'include_in_funnel'"))
        if result.fetchone():
            print("Column 'include_in_funnel' already exists in 'kanban_stages'. Skipping.")
            return

        print("Adding 'include_in_funnel' column to 'kanban_stages' table...")
        conn.execute(text("ALTER TABLE kanban_stages ADD COLUMN include_in_funnel BOOLEAN DEFAULT TRUE"))
        print("Column added successfully.")

if __name__ == "__main__":
    upgrade()
