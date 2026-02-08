from config.database import init_db
import app.models # Importar modelos para garantir que sejam registrados no Base

if __name__ == "__main__":
    print("Criando tabelas faltantes...")
    init_db()
    print("Tabelas criadas com sucesso.")
