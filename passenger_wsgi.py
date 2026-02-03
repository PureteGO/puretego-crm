import sys
import os

# --- PURETEGO SMART IMPORT FIX ---
# Passenger runs Python 3.x but might not load 'venv' automatically.
# We explicitly inject the venv site-packages into sys.path.

cwd = os.getcwd()
venv_lib = os.path.join(cwd, 'venv', 'lib')

if os.path.exists(venv_lib):
    # Find the pythonX.X folder inside lib
    for item in os.listdir(venv_lib):
        site_packages = os.path.join(venv_lib, item, 'site-packages')
        if os.path.exists(site_packages):
            sys.path.insert(0, site_packages)
            break

# ---------------------------------

from app import create_app
from config.settings import ProductionConfig

application = create_app(ProductionConfig)
