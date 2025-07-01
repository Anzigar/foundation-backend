#!/bin/bash

# Simple script to fix database tables for production

echo "🔧 Fixing database tables..."

# Run the table fix script inside the container
docker exec foundation-api python fix_tables.py

if [ $? -eq 0 ]; then
    echo "✅ Database tables fixed successfully!"
    echo "🔄 Restarting the backend container..."
    docker restart foundation-api
    echo "✅ Backend restarted. Your API should now work correctly!"
else
    echo "❌ Failed to fix database tables. Check the logs above."
    exit 1
fi
