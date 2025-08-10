#!/bin/bash

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

# Wait for services to start
log "Waiting for containers to start..."
sleep 15

# Check if containers are running
log "Checking container status..."
docker compose ps

# Verify database connection and tables
log "� Verifying database setup..."
HEALTH_CHECK=$(docker exec foundation-api python -c "
import os
from sqlalchemy import create_engine, inspect

def get_database_url():
    host = os.getenv('POSTGRES_HOST', 'database')
    port = os.getenv('POSTGRES_PORT', '5432')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    database = os.getenv('POSTGRES_DB', 'website_db')
    return f'postgresql://{user}:{password}@{host}:{port}/{database}'

try:
    engine = create_engine(get_database_url())
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f'✅ Database connected successfully! Found {len(tables)} tables.')
    exit(0)
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
")

if [ $? -eq 0 ]; then
    log "✅ Database connection verified!"
    
    # Fix events sequence first
    log "🔧 Fixing events auto-increment sequence..."
    docker exec foundation-api python3 fix_events_sequence.py
    if [ $? -eq 0 ]; then
        log "✅ Events sequence fixed successfully!"
    else
        log "❌ Events sequence fix failed - continuing anyway"
    fi
    
    # Run the events migration
    log "🔄 Running events migration to UUID..."
    docker exec foundation-api python3 migrate_events_to_uuid.py
    if [ $? -eq 0 ]; then
        log "✅ Events migration completed successfully!"
    else
        log "❌ Events migration failed - continuing anyway"
    fi
    
    # Wait for container to be fully ready
    log "⏳ Waiting for backend container to be ready..."
    sleep 10
    
    log "🧪 Testing API endpoints..."
    
    # Test the API endpoints
    log "Testing /api/projects/..."
    PROJECTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/projects/)
    if [ "$PROJECTS_STATUS" = "200" ]; then
        log "✅ Projects API working (HTTP $PROJECTS_STATUS)"
    else
        log "❌ Projects API failing (HTTP $PROJECTS_STATUS)"
    fi
    
    log "Testing /api/news/..."
    NEWS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/news/)
    if [ "$NEWS_STATUS" = "200" ]; then
        log "✅ News API working (HTTP $NEWS_STATUS)"
    else
        log "❌ News API failing (HTTP $NEWS_STATUS)"
    fi
    
    log "Testing /api/events/..."
    EVENTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/events/)
    if [ "$EVENTS_STATUS" = "200" ]; then
        log "✅ Events API working (HTTP $EVENTS_STATUS)"
    else
        log "❌ Events API failing (HTTP $EVENTS_STATUS)"
    fi
    
    log ""
    log "🎉 Production environment setup complete!"
    log "🌐 Your API is available at: https://backend.pathwaysfoundationforthepoor.org"
    log "📋 API Documentation: https://backend.pathwaysfoundationforthepoor.org/docs"
    log ""
    
    # Final status check
    if [ "$PROJECTS_STATUS" = "200" ] && [ "$NEWS_STATUS" = "200" ] && [ "$EVENTS_STATUS" = "200" ]; then
        log "🎊 All API endpoints are working correctly!"
    else
        log "⚠️  Some API endpoints may need additional attention."
        log "📝 Check container logs with: docker logs foundation-api"
    fi
    
else
    log "❌ Failed to fix database tables. Check the logs above."
    log "📊 Checking container status..."
    docker compose ps
    log ""
    log "📝 Checking backend container logs..."
    docker logs foundation-api --tail 50
    exit 1
fi
