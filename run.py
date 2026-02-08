import sys
import os
import traceback
from flask import Flask

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from dotenv import load_dotenv
    load_dotenv()
    
    from app import create_app
    from config.settings import ProductionConfig
    
    # Tentativa de criar o app real
    application = create_app(ProductionConfig)
    app = application
    
except Exception as e:
    # Se falhar, cria um app de erro para diagnóstico
    error_info = traceback.format_exc()
    application = Flask(__name__)
    
    @application.route('/')
    @application.route('/<path:path>')
    def diagnostic_error(path=None):
        return f"""
        <html>
            <body style="font-family: sans-serif; padding: 20px; line-height: 1.6;">
                <h1 style="color: #d9534f;">Erro na Inicialização do Aplicativo</h1>
                <p>O servidor Python não conseguiu carregar o CRM. Isso geralmente acontece por falta de bibliotecas ou erro de config.</p>
                <div style="background: #f8f9fa; border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
                    <strong>Erro detectado:</strong>
                    <pre style="white-space: pre-wrap; color: #c7254e;">{str(e)}</pre>
                </div>
                <h3>Rastro do Erro (Traceback):</h3>
                <pre style="background: #222; color: #eee; padding: 15px; border-radius: 5px; overflow-x: auto;">{error_info}</pre>
                <p><strong>Dica:</strong> Verifique se clicou em 'Run Pip Install' no cPanel.</p>
            </body>
        </html>
        """
    app = application

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=5000)
