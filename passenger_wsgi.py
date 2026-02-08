import sys
import os

# --- PURETEGO PRODUCTION FIX ---
# Precisamos apontar para o virtualenv correto no servidor
# Baseado no Setup Python App: /home2/appmaps2go/virtualenv/maps2go_crm/3.10/

venv_base = '/home2/appmaps2go/virtualenv/maps2go_crm/3.10/lib'

if os.path.exists(venv_base):
    for item in os.listdir(venv_base):
        # Geralmente a pasta é 'python3.10'
        site_packages = os.path.join(venv_base, item, 'site-packages')
        if os.path.exists(site_packages):
            sys.path.insert(0, site_packages)
            break

# Adicionar a pasta do app ao sys.path
sys.path.insert(0, '/home2/appmaps2go/maps2go_crm')

# Importar o app
from app import create_app
from config.settings import ProductionConfig

# O Passenger espera uma variável chamada 'application' ou o nome definido no cPanel
application = create_app(ProductionConfig)
app = application # Fallback para o entry point definido como 'app' no cPanel
