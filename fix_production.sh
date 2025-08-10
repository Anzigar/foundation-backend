#!/bin/bash

# Comprehensive script to fix database tables and router issues for production

echo "🔧 Fixing database tables and router issues..."

# Step 1: Fix the projects router queries
echo "📝 Fixing projects router queries..."
docker exec foundation-api sed -i 's/i\."primary" = true/i.primary_image = true/g' /app/projects/router.py
docker exec foundation-api sed -i 's/"primary",/"primary_image",/g' /app/projects/router.py
docker exec foundation-api sed -i 's/"primary" = false/primary_image = false/g' /app/projects/router.py
docker exec foundation-api sed -i 's/"primary" = %s/primary_image = %s/g' /app/projects/router.py

# Step 2: Run the table fix script inside the container
echo "🗃️  Creating missing database tables..."
docker exec foundation-api python fix_tables.py

# Step 3: Add the missing column to project_images table
echo "🔧 Adding missing primary_image column..."
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
    # Update existing primary column to primary_image
    conn.execute(text('UPDATE project_images SET primary_image = COALESCE(\"primary\", FALSE) WHERE primary_image IS NULL'))
    conn.commit()
    print('✅ Fixed project_images table columns')
"

# Step 4: Check if all tables exist now
echo "🔍 Verifying tables exist..."
docker exec foundation-api python -c "
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
else:
    print('✅ All required tables exist!')

for table in tables:
    print(f'  - {table}')
"

if [ $? -eq 0 ]; then
    echo "✅ Database tables fixed successfully!"
    echo "🔄 Restarting the backend container..."
    docker restart foundation-api
    
    # Wait for container to be ready
    echo "⏳ Waiting for container to restart..."
    sleep 10
    
    echo "🧪 Testing API endpoints..."
    
    # Test the API endpoints
    echo "Testing /api/projects/..."
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/projects/ | grep -q "200" && echo "✅ Projects API working" || echo "❌ Projects API still failing"
    
    echo "Testing /api/news/..."
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/news/ | grep -q "200" && echo "✅ News API working" || echo "❌ News API still failing"
    
    echo "Testing /api/events/..."
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/events/ | grep -q "200" && echo "✅ Events API working" || echo "❌ Events API still failing"
    
    echo ""
    echo "🎉 Production environment should now be working!"
    echo "🌐 Your API is available at: https://backend.pathwaysfoundationforthepoor.org"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Test all API endpoints via https://backend.pathwaysfoundationforthepoor.org/api/docs"
    echo "  2. Create some test data via the API"
    echo "  3. Connect your frontend to the API"
    
else
    echo "❌ Failed to fix database tables. Check the logs above."
    echo "📊 Checking container status..."
    docker ps | grep foundation
    echo ""
    echo "📝 Checking container logs..."
    docker logs foundation-api --tail 50
    exit 1
fi
