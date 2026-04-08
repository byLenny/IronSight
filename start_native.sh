#!/bin/bash
echo "=== IronSight Native Startup ==="

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
echo "Access the dashboard at: http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000
