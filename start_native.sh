#!/bin/bash
echo "=== IronSight Native Startup ==="

# Load nvm if it exists
if [ -z "$NVM_DIR" ]; then
    export NVM_DIR="$HOME/.nvm"
fi
if [ -s "$NVM_DIR/nvm.sh" ]; then
    \. "$NVM_DIR/nvm.sh"
    nvm install
    nvm use
else
    echo "nvm is not installed. Please install nvm first: https://github.com/nvm-sh/nvm"
    exit 1
fi

echo "Building frontend..."
(cd frontend && npm install && npm run build)

if [ $? -ne 0 ]; then
    echo "Frontend build failed! Aborting."
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "Error: Python pip is not installed or not in PATH."
    exit 1
fi

echo "Installing Python dependencies..."
pip install -r requirements.txt

# Set default password if the user hasn't already exported one
export ADMIN_PASSWORD=${ADMIN_PASSWORD:-"secretpassword"}

echo "Starting Uvicorn Web Server..."
echo "Access the dashboard at: http://localhost:8008"
uvicorn app.main:app --host 0.0.0.0 --port 8008