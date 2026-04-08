Write-Host "=== IronSight Native Startup ===" -ForegroundColor Cyan

# Check if pip is available
if (-not (Get-Command "pip" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python pip is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

Write-Host "Installing Python dependencies..."
pip install -r requirements.txt

# Set default password if not provided
if (-not $env:ADMIN_PASSWORD) {
    $env:ADMIN_PASSWORD = "secretpassword"
}

Write-Host "Starting Uvicorn Web Server..."
Write-Host "Access the dashboard at: http://localhost:8000" -ForegroundColor Green
uvicorn app.main:app --host 0.0.0.0 --port 8000
