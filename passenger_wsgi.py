import sys
import os

# --- PURETEGO SMART IMPORT FIX ---
# Passenger runs Python 3.x but might not load 'venv' automatically.
# We explicitly inject the venv site-packages into sys.path.

# --- PURETEGO PRODUCTION FIX ---
# Explicitly point to the cPanel Virtual Environment where we installed dependencies
# Found at: /home2/crmpuretego/virtualenv/repositories/puretego-crm/3.11/

cpanel_venv = '/home2/crmpuretego/virtualenv/repositories/puretego-crm/3.11/lib'

# Find the python version folder (e.g., python3.11)
if os.path.exists(cpanel_venv):
    for item in os.listdir(cpanel_venv):
        site_packages = os.path.join(cpanel_venv, item, 'site-packages')
        if os.path.exists(site_packages):
            sys.path.insert(0, site_packages)
            break
else:
    # Fallback: try local venv (dev environment)
    cwd = os.getcwd()
    venv_lib = os.path.join(cwd, 'venv', 'lib')
    if os.path.exists(venv_lib):
         for item in os.listdir(venv_lib):
            site_packages = os.path.join(venv_lib, item, 'site-packages')
            if os.path.exists(site_packages):
                sys.path.insert(0, site_packages)
                break

# ---------------------------------

from app import create_app
from config.settings import ProductionConfig

application = create_app(ProductionConfig)
