
import os
import sys

# Adiciona o diretório raiz ao path para importar as configurações
sys.path.append(os.getcwd())

from config.database import engine
from sqlalchemy import text

def migrate():
    print("Iniciando migração da tabela project_tickets...")
    
    with engine.connect() as conn:
        # 1. Adicionar colunas se não existirem
        columns = [
            ("assigned_by_id", "INTEGER REFERENCES users(id)"),
            ("verification_required", "BOOLEAN DEFAULT FALSE"),
            ("approved_at", "DATETIME"),
            ("approved_by_id", "INTEGER REFERENCES users(id)"),
            ("rejection_comment", "TEXT"),
            ("assigned_comment", "TEXT")
        ]
        
        for col_name, col_type in columns:
            try:
                # SQLite doesn't support 'IF NOT EXISTS' for columns directly in older versions, 
                # but we can check if it exists or just try and catch.
                print(f"Adicionando coluna {col_name}...")
                conn.execute(text(f"ALTER TABLE project_tickets ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception as e:
                # Se der erro provavelmente é porque a coluna já existe
                print(f"Erro/Aviso na coluna {col_name}: {e}")
                
    print("Migração concluída.")

if __name__ == "__main__":
    migrate()
