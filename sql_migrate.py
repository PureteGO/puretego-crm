from config.database import engine
from sqlalchemy import text

statements = [
    "ALTER TABLE services ADD COLUMN company_id INT",
    "ALTER TABLE services ADD CONSTRAINT fk_services_company FOREIGN KEY (company_id) REFERENCES companies(id)",
    "ALTER TABLE service_packages ADD COLUMN company_id INT",
    "ALTER TABLE service_packages ADD CONSTRAINT fk_packages_company FOREIGN KEY (company_id) REFERENCES companies(id)"
]

def run_sql():
    with engine.connect() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
                print(f"Executed: {stmt}")
            except Exception as e:
                print(f"Failed: {stmt} - {str(e)}")
        conn.commit()

if __name__ == "__main__":
    run_sql()
