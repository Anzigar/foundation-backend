#!/bin/bash
set -e

echo "🔧 Fixing missing database tables for production..."

# Stop the backend service
echo "Stopping backend service..."
docker-compose stop backend || true

# Run the SQL script to create missing tables
echo "Creating missing tables..."
docker-compose exec -T database psql -U postgres -d website_db < fix_tables.sql

# Check if tables were created
echo "Verifying table creation..."
docker-compose exec -T database psql -U postgres -d website_db -c "\dt" | grep -E "(users|news_articles|events|projects|contacts)"

# Restart the backend service
echo "Restarting backend service..."
docker-compose up -d backend

echo "✅ Database tables fixed! Checking logs..."
sleep 5
docker-compose logs --tail=20 backend
