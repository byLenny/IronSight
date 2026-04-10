# Check for nvm
if (!(Get-Command nvm -ErrorAction SilentlyContinue)) {
    Write-Host "nvm is not installed. Please install nvm-windows: https://github.com/coreybutler/nvm-windows" -ForegroundColor Red
    exit 1
}

Write-Host "Installing and using Node.js 22.22 via nvm..."
nvm install 22.22
nvm use 22.22

# Check for docker
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "docker is not installed. Please install Docker." -ForegroundColor Red
    exit 1
}

echo "Building frontend..."
Push-Location frontend
npm install
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
npm run build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Pop-Location

echo "Starting Standalone IronSight Server..."
docker compose up --build
