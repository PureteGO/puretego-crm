import sys
import os

# Adicionar o diretório raiz ao path para importar as configurações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import engine, Base
from sqlalchemy import text, inspect

def run_migration():
    print("Iniciando migração de categorias (MySQL)...")
    
    with engine.connect() as conn:
        # 1. Criar a tabela payable_categories se não existir
        print("Criando tabela payable_categories...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payable_categories (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                company_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                color VARCHAR(20) DEFAULT '#6c757d',
                FOREIGN KEY(company_id) REFERENCES companies(id)
            )
        """))
        
        # 2. Adicionar a coluna category_id na tabela payables se não existir
        print("Verificando coluna category_id em payables...")
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('payables')]
        
        if 'category_id' not in columns:
            print("Adicionando coluna category_id...")
            conn.execute(text("ALTER TABLE payables ADD COLUMN category_id INTEGER REFERENCES payable_categories(id)"))
        else:
            print("Coluna category_id já existe.")
            
        conn.commit()
        print("Migração concluída com sucesso!")

if __name__ == "__main__":
    run_migration()
