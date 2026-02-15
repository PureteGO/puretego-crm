
import sqlalchemy as sa
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    # Fallback to individual variables
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '3306')
    name = os.getenv('DB_NAME', 'puretego_crm')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASS', '')
    
    if user and password and name:
        DATABASE_URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"
        print(f"Using constructed DATABASE_URL for {host}")
    else:
        print("Error: DATABASE_URL not found and DB_* variables incomplete.")
        exit(1)
else:
    print("Using provided DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL)

def run_migration():
    if not DATABASE_URL:
        print("Database configuration missing.")
        return

    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            print("Starting Task Module v2 Migration...")

            # 1. Update 'tasks' table
            print("Checking 'tasks' table columns...")
            # Column definitions to check/add
            # Format: (column_name, definition, after_column)
            # We don't strictly need 'after_column' but it helps organization if supported by DB (MySQL does)
            
            # Additional columns for Task V2
            task_columns = [
                ("verification_required", "BOOLEAN DEFAULT FALSE"),
                ("approved_at", "DATETIME DEFAULT NULL"),
                ("approved_by_id", "INT DEFAULT NULL"),
                ("rejection_comment", "TEXT DEFAULT NULL"),
                ("completed_by_id", "INT DEFAULT NULL"),
                ("phase", "VARCHAR(50) DEFAULT NULL"), # For project tasks
                ("is_onboarding", "BOOLEAN DEFAULT FALSE") # For project tasks
            ]

            for col_name, col_def in task_columns:
                try:
                    # Check if column exists
                    # This query is specific to MySQL which seems to be the target DB
                    result = conn.execute(text(f"SHOW COLUMNS FROM tasks LIKE '{col_name}'"))
                    if result.fetchone():
                        print(f" - Column '{col_name}' already exists.")
                    else:
                        print(f" - Adding column '{col_name}'...")
                        conn.execute(text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_def}"))
                        
                        # If it's a foreign key column (ends with _id and is new), add constraint
                        # simplistic check, might need manual adjustment if complex
                        if col_name.endswith("_id") and "by_id" in col_name:
                             try:
                                fk_name = f"fk_tasks_{col_name}"
                                # Check if constraint exists effectively (or just try adding and ignore error)
                                # MySQL doesn't have "IF NOT EXISTS" for constraints in standard ALTER TABLE easily
                                # We'll wrap in try-except
                                print(f"   - Attempting to add FK {fk_name}...")
                                conn.execute(text(f"ALTER TABLE tasks ADD CONSTRAINT {fk_name} FOREIGN KEY ({col_name}) REFERENCES users(id)"))
                             except Exception as e:
                                print(f"   - Note: FK creation might have failed (exists?): {e}")
                        
                        conn.commit()
                        print(f"   Success!")
                except Exception as e:
                    print(f"   Error processing '{col_name}': {e}")


            # 2. Create 'notifications' table if not exists
            print("Checking 'notifications' table...")
            try:
                result = conn.execute(text("SHOW TABLES LIKE 'notifications'"))
                if result.fetchone():
                    print(" - Table 'notifications' already exists.")
                else:
                    print(" - Creating table 'notifications'...")
                    conn.execute(text("""
                        CREATE TABLE notifications (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            company_id INT NOT NULL,
                            user_id INT NOT NULL,
                            title VARCHAR(255) NOT NULL,
                            message TEXT,
                            notification_type VARCHAR(50) DEFAULT 'info',
                            reference_type VARCHAR(50) DEFAULT NULL,
                            reference_id INT DEFAULT NULL,
                            is_read BOOLEAN DEFAULT FALSE,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            INDEX idx_notifications_user_id (user_id),
                            INDEX idx_notifications_company_id (company_id),
                            INDEX idx_notifications_is_read (is_read),
                            FOREIGN KEY (company_id) REFERENCES companies(id),
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                    """))
                    conn.commit()
                    print("   Success!")
            except Exception as e:
                print(f"   Error checking/creating 'notifications' table: {e}")

            print("Migration completed.")
            
    except Exception as e:
        print(f"Critical error connecting to database: {e}")

if __name__ == "__main__":
    run_migration()
