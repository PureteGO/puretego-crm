from config.database import engine
from sqlalchemy import text

def check_and_fix():
    tables = ['services', 'service_packages']
    with engine.connect() as conn:
        for table in tables:
            print(f"Checking table: {table}")
            try:
                res = conn.execute(text(f"SHOW COLUMNS FROM {table} LIKE 'company_id'"))
                column = res.fetchone()
                if not column:
                    print(f"Adding company_id to {table}")
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN company_id INT"))
                    conn.execute(text(f"ALTER TABLE {table} ADD CONSTRAINT fk_{table}_company FOREIGN KEY (company_id) REFERENCES companies(id)"))
                    print(f"Successfully added company_id to {table}")
                else:
                    print(f"company_id already exists in {table}")
            except Exception as e:
                print(f"Error checking/fixing {table}: {str(e)}")
        conn.commit()

if __name__ == "__main__":
    check_and_fix()
