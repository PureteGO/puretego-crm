#!/bin/bash

# Define app directory
APP_DIR="~/puretego-crm"

echo "=== Updating Production Environment ==="
cd $APP_DIR

# Activate Virtual Environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install Dependencies
echo "Installing dependencies..."
pip install flask flask-sqlalchemy sqlalchemy pymysql bcrypt google-search-results python-dotenv

# Restart Application (touching tmp/restart.txt or passenger_wsgi.py usually triggers a restart in cPanel)
echo "Restarting application..."
touch tmp/restart.txt 2>/dev/null || touch passenger_wsgi.py

echo "=== Update Complete ==="
echo "Dependencies installed and app restarted."
