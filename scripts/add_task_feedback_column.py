
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def add_feedback_column():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'puretego_crm')
    port = int(os.getenv('DB_PORT', 3306))

    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=db_name,
        port=port,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection.cursor() as cursor:
            print("Adding 'assigned_comment' column to 'tasks' table...")
            sql = "ALTER TABLE tasks ADD COLUMN assigned_comment TEXT NULL AFTER completed_at;"
            cursor.execute(sql)
            connection.commit()
            print("Successfully added 'assigned_comment' column.")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("Column 'assigned_comment' already exists.")
        else:
            print(f"Error: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    add_feedback_column()
