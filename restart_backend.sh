#!/bin/bash

# Simple script to restart the backend container with updated code

echo "🔄 Restarting backend container with updated code..."

# Stop and restart the backend container
docker-compose stop api
docker-compose up -d api

echo "✅ Backend container restarted"

# Wait a moment for the container to start
sleep 5

# Check container status
echo "📊 Container status:"
docker-compose ps api

# Check if the API is responding
echo "🔍 Testing API health..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/docs || echo "API not yet available"
