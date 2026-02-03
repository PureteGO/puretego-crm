#!/bin/bash

# Setup Script for PureteGO CRM on cPanel
# Usage: ./setup_crm.sh

echo ">>> Starting PureteGO CRM Setup..."

# 1. Define Paths
APP_ROOT=$(pwd)
VENV_DIR="$APP_ROOT/venv"
PYTHON_BIN="/usr/bin/python3" # Default, may need adjustment based on cPanel

# 2. Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 could not be found."
    exit 1
fi

echo ">>> Python Version: $(python3 --version)"

# 3. Create Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo ">>> Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo ">>> Virtual environment already exists."
fi

# 4. Activate & Install Dependencies
source "$VENV_DIR/bin/activate"
echo ">>> Installing dependencies..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "WARNING: requirements.txt not found!"
fi

# 5. Directory Structure
echo ">>> Ensuring directory structure..."
mkdir -p app/static
mkdir -p app/templates
mkdir -p instance
mkdir -p tmp

# 6. Create Passenger Startup File if missing
if [ ! -f "passenger_wsgi.py" ]; then
    echo ">>> Creating default passenger_wsgi.py..."
    cat <<EOF > passenger_wsgi.py
import sys
import os

# Create a clear entry point for debugging
sys.path.append(os.getcwd())
from app import create_app

application = create_app()
EOF
fi

# 7. Final Check
echo ">>> Setup Complete!"
echo "Run 'source venv/bin/activate' to enter the environment."
