#!/bin/bash

echo "🔧 Foundation Backend - Complete Database and UUID Fix"
echo "====================================================="

echo "📊 Current service status:"
docker-compose ps

echo ""
echo "🔄 Restarting backend service to apply UUID fixes..."
docker-compose restart backend

echo ""
echo "⏱️  Waiting for service to start..."
sleep 10

echo ""
echo "🧪 Testing UUID fix with news API..."

# Test the news endpoint that was failing
echo "Creating a test news article..."
curl -X POST "http://localhost:8000/api/news/" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Test UUID Fix Article",
       "content": "This is a test article to verify UUID handling is working correctly.",
       "excerpt": "Test article for UUID fix verification",
       "source": "System Test",
       "published": true,
       "featured": false,
       "tags": "test,uuid,fix"
     }' \
     -w "\nHTTP Status: %{http_code}\n" || echo "❌ News API test failed"

echo ""
echo "🧪 Testing projects API..."
curl -X GET "http://localhost:8000/api/projects/" \
     -w "\nHTTP Status: %{http_code}\n" || echo "❌ Projects API test failed"

echo ""
echo "🧪 Testing authentication API..."
curl -X POST "http://localhost:8000/api/auth/register/" \
     -H "Content-Type: application/json" \
     -d '{
       "full_name": "Test User",
       "email": "test@example.com",
       "password": "testpassword123"
     }' \
     -w "\nHTTP Status: %{http_code}\n" || echo "❌ Auth API test failed"

echo ""
echo "📋 Final service status:"
docker-compose ps

echo ""
echo "📝 Recent logs from backend:"
docker-compose logs --tail=10 backend

echo ""
echo "✅ UUID and database fixes deployment completed!"
echo "If you see HTTP 200/201 responses above, the fixes are working correctly."
