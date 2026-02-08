import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def fix_schema():
    host = os.environ.get('DB_HOST', 'localhost')
    port = int(os.environ.get('DB_PORT', 3306))
    database = os.environ.get('DB_NAME', 'puretego_crm')
    user = os.environ.get('DB_USER', 'root')
    password = os.environ.get('DB_PASS', '')
    
    database_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    
    engine = create_engine(database_url)
    
    # Colunas para adicionar na tabela 'companies'
    columns_to_add = [
        ("workflow_mode", "VARCHAR(50) DEFAULT 'lean'"),
        ("plan_tier", "VARCHAR(50) DEFAULT 'solo'"),
        ("plan_config", "JSON NULL"),
        ("commission_closer_rate", "DECIMAL(5, 2) DEFAULT 10.00"),
        ("commission_sdr_rate", "DECIMAL(5, 2) DEFAULT 2.00"),
        ("smtp_server", "VARCHAR(255) NULL"),
        ("smtp_port", "INT DEFAULT 587"),
        ("smtp_use_tls", "BOOLEAN DEFAULT TRUE"),
        ("smtp_username", "VARCHAR(255) NULL"),
        ("smtp_password", "VARCHAR(255) NULL"),
        ("smtp_from_email", "VARCHAR(255) NULL"),
        ("smtp_from_name", "VARCHAR(255) NULL"),
        ("currency_symbol", "VARCHAR(5) DEFAULT 'Gs'")
    ]

    with engine.connect() as conn:
        # Verificar colunas existentes
        result = conn.execute(text("DESCRIBE companies"))
        existing_columns = [row[0] for row in result]
        
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                print(f"Adding column {col_name}...")
                try:
                    conn.execute(text(f"ALTER TABLE companies ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"✅ Column {col_name} added.")
                except Exception as e:
                    print(f"❌ Error adding {col_name} to companies: {e}")
            else:
                print(f"✔ Column {col_name} already exists in companies.")

        # Colunas para adicionar na tabela 'users'
        user_columns = [
            ("base_salary", "DECIMAL(10, 2) DEFAULT 0.00"),
            ("receives_commission", "BOOLEAN DEFAULT TRUE"),
            ("reset_token", "VARCHAR(100) NULL"),
            ("reset_token_expires", "DATETIME NULL")
        ]
        
        result = conn.execute(text("DESCRIBE users"))
        existing_user_columns = [row[0] for row in result]
        
        for col_name, col_type in user_columns:
            if col_name not in existing_user_columns:
                print(f"Adding column {col_name} to users...")
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"✅ Column {col_name} added to users.")
                except Exception as e:
                    print(f"❌ Error adding {col_name} to users: {e}")
            else:
                print(f"✔ Column {col_name} already exists in users.")

if __name__ == "__main__":
    fix_schema()
