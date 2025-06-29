#!/bin/sh

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Setup tasks
log "Running setup tasks..."

# Create proxy network if it doesn't exist
if ! docker network ls | grep -q "proxy"; then
    log "Creating Docker network 'proxy'..."
    docker network create proxy || log "Network might already exist or insufficient permissions"
fi

# compose down
log "Stopping and removing existing containers..."
docker compose down || log "No existing containers to stop or remove"

# Ensure entrypoint.sh has execute permissions
log "Setting execute permissions on entrypoint.sh..."
chmod +x entrypoint.sh

# Create and set permissions for acme.json
log "Setting up SSL certificate storage..."
touch acme.json && chmod 600 acme.json

# Start the application
log "Starting the application..."
docker compose up --build -d

# Wait a moment for services to start
sleep 2

# Check if containers are running
log "Checking container status..."
docker compose ps

log "Service started successfully!"
