import sys
import os

# --- PURETEGO PRODUCTION BOOTSTRAP 3.11 ---
# Direcionar erros para um arquivo para podermos ler se der 500
sys.stderr = open(os.path.expanduser('~/error_log_python.txt'), 'w')

# Caminho do virtualenv 3.11 que o cPanel criou
venv_path = '/home2/puretego/virtualenv/gbpcheck.puretego.online/3.11/lib/python3.11/site-packages'
sys.path.insert(0, venv_path)

# Caminho da aplicação
sys.path.insert(0, '/home2/puretego/gbpcheck.puretego.online')

try:
    from app import create_app
    from config.settings import ProductionConfig
    
    # O cPanel configurou o entry point como 'app'
    app = create_app(ProductionConfig)
    application = app
    
except Exception as e:
    import traceback
    with open(os.path.expanduser('~/gbpcheck.puretego.online/startup_error.txt'), 'w') as f:
        f.write(traceback.format_exc())
    raise
