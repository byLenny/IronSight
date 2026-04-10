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

echo "Starting Standalone IronSight Server..."
docker compose up --build

