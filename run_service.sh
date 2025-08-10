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

# ==== PRODUCTION FIXES ====
log "🔧 Applying production fixes and database repairs..."

# Step 1: Fix the projects router queries to use correct column names
log "📝 Fixing projects router queries..."
docker exec foundation-api sed -i 's/i\."primary" = true/i.primary_image = true/g' /app/projects/router.py
docker exec foundation-api sed -i 's/"primary",/"primary_image",/g' /app/projects/router.py
docker exec foundation-api sed -i 's/"primary" = false/primary_image = false/g' /app/projects/router.py
docker exec foundation-api sed -i 's/"primary" = %s/primary_image = %s/g' /app/projects/router.py

# Step 2: Run the table fix script inside the container to create missing tables
log "🗃️  Creating missing database tables and columns..."
docker exec foundation-api python fix_tables.py

# Step 3: Add the missing primary_image column to project_images table
log "🔧 Adding missing primary_image column to project_images table..."
docker exec foundation-api python -c "
import os
from sqlalchemy import create_engine, text

def get_database_url():
    host = os.getenv('POSTGRES_HOST', 'database')
    port = os.getenv('POSTGRES_PORT', '5432')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    database = os.getenv('POSTGRES_DB', 'website_db')
    return f'postgresql://{user}:{password}@{host}:{port}/{database}'

engine = create_engine(get_database_url())
with engine.connect() as conn:
    # Add the missing primary_image column if it doesn't exist
    conn.execute(text('ALTER TABLE project_images ADD COLUMN IF NOT EXISTS primary_image BOOLEAN DEFAULT FALSE'))
    # Update existing primary column to primary_image if primary column exists
    try:
        conn.execute(text('UPDATE project_images SET primary_image = COALESCE(\"primary\", FALSE) WHERE primary_image IS NULL'))
    except:
        pass  # primary column might not exist
    conn.commit()
    print('✅ Fixed project_images table columns')
"

# Step 4: Verify all required tables exist
log "🔍 Verifying all required tables exist..."
TABLES_CHECK=$(docker exec foundation-api python -c "
import os
from sqlalchemy import create_engine, inspect

def get_database_url():
    host = os.getenv('POSTGRES_HOST', 'database')
    port = os.getenv('POSTGRES_PORT', '5432')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    database = os.getenv('POSTGRES_DB', 'website_db')
    return f'postgresql://{user}:{password}@{host}:{port}/{database}'

engine = create_engine(get_database_url())
inspector = inspect(engine)
tables = inspector.get_table_names()

required_tables = ['users', 'news_articles', 'events', 'projects', 'contacts', 'project_images', 'blog_posts', 'blog_categories', 'media']
missing = [t for t in required_tables if t not in tables]

if missing:
    print(f'❌ Still missing tables: {missing}')
    exit(1)
else:
    print('✅ All required tables exist!')
    for table in sorted(tables):
        print(f'  - {table}')
    exit(0)
")

if [ $? -eq 0 ]; then
    log "✅ Database tables and columns fixed successfully!"
    log "🔄 Restarting the backend container to apply router fixes..."
    docker restart foundation-api
    
    # Wait for container to be ready
    log "⏳ Waiting for backend container to restart..."
    sleep 15
    
    log "🧪 Testing API endpoints to verify everything is working..."
    
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
