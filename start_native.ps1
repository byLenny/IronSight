Write-Host "=== IronSight Native Startup ===" -ForegroundColor Cyan

# Check for nvm
if (!(Get-Command nvm -ErrorAction SilentlyContinue)) {
    Write-Host "nvm is not installed. Please install nvm-windows: https://github.com/coreybutler/nvm-windows" -ForegroundColor Red
    exit 1
}

$NodeVersion = Get-Content .nvmrc
Write-Host "Installing and using Node.js $NodeVersion via nvm..."
nvm install $NodeVersion
nvm use $NodeVersion

echo "Building frontend..."
Push-Location frontend
npm install
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
npm run build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Pop-Location


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
Write-Host "Access the dashboard at: http://localhost:8008" -ForegroundColor Green
uvicorn app.main:app --host 0.0.0.0 --port 8008
