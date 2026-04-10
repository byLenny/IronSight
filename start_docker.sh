#!/bin/bash

# Load nvm if it exists
if [ -z "$NVM_DIR" ]; then
    export NVM_DIR="$HOME/.nvm"
fi
if [ -s "$NVM_DIR/nvm.sh" ]; then
    \. "$NVM_DIR/nvm.sh"
else
    echo "nvm is not installed. Please install nvm first: https://github.com/nvm-sh/nvm"
    exit 1
fi

echo "Installing and using Node.js 22.22 via nvm..."
nvm install 22.22
nvm use 22.22

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "docker could not be found. Please install Docker."
    exit 1
fi

echo "Building frontend..."
(cd frontend && npm install && npm run build)

if [ $? -ne 0 ]; then
    echo "Frontend build failed! Aborting."
    exit 1
fi

echo "Starting Standalone IronSight Server..."
docker compose up --build
