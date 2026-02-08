"""
PURETEGO CRM - Application Entry Point
Arquivo principal para executar a aplicação
"""

from dotenv import load_dotenv
load_dotenv()  # Carrega variáveis do .env

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Executar em modo de desenvolvimento
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
