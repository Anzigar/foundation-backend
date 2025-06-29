#!/usr/bin/env python3
"""
Deployment verification script for Foundation Backend.
This script checks that all endpoints are working and the database is properly set up.
"""

import os
import sys
import asyncio
import aiohttp
from sqlalchemy import create_engine, text
import json
from datetime import datetime


def get_api_base_url():
    """Get the API base URL from environment or use default."""
    return os.getenv('API_BASE_URL', 'http://localhost:8000')


def get_db_connection_params():
    """Get database connection parameters from environment variables."""
    params = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'database': os.getenv('POSTGRES_DB', 'foundation'),
    }
    
    password = os.getenv('POSTGRES_PASSWORD')
    if password:
        params['password'] = password
    
    return params


def create_sync_db_url(params):
    """Create synchronous database URL."""
    if 'password' in params:
        return f"postgresql://{params['user']}:{params['password']}@{params['host']}:{params['port']}/{params['database']}"
    else:
        return f"postgresql://{params['user']}@{params['host']}:{params['port']}/{params['database']}"


def test_database_connection():
    """Test database connection and verify tables exist."""
    try:
        print("Testing database connection...")
        
        params = get_db_connection_params()
        sync_url = create_sync_db_url(params)
        engine = create_engine(sync_url)
        
        with engine.connect() as conn:
            # Test basic connection
            result = conn.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
            print("✓ Database connection successful")
            
            # Check if tables exist
            expected_tables = [
                'users', 'blog_categories', 'blog_posts', 'news_articles',
                'events', 'projects', 'contacts', 'media'
            ]
            
            for table in expected_tables:
                result = conn.execute(text(f"SELECT to_regclass('public.{table}')"))
                table_exists = result.fetchone()[0] is not None
                if table_exists:
                    print(f"✓ Table '{table}' exists")
                else:
                    print(f"✗ Table '{table}' missing")
                    return False
            
            # Check sample data counts
            for table in expected_tables:
                if table != 'alembic_version':
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    print(f"  → {table}: {count} records")
            
            return True
            
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False


async def test_api_endpoints():
    """Test API endpoints to ensure they're working."""
    base_url = get_api_base_url()
    
    endpoints = [
        ('/', 'GET', 'Root endpoint'),
        ('/health', 'GET', 'Health check'),
        ('/docs', 'GET', 'API Documentation'),
        ('/api/v1/blog/posts', 'GET', 'Blog posts'),
        ('/api/v1/news/articles', 'GET', 'News articles'),
        ('/api/v1/events', 'GET', 'Events'),
        ('/api/v1/projects', 'GET', 'Projects'),
    ]
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            print(f"\nTesting API endpoints at {base_url}...")
            
            for endpoint, method, description in endpoints:
                url = f"{base_url}{endpoint}"
                try:
                    async with session.request(method, url) as response:
                        if response.status == 200:
                            print(f"✓ {description}: {response.status}")
                        else:
                            print(f"✗ {description}: {response.status}")
                            return False
                except Exception as e:
                    print(f"✗ {description}: Failed - {e}")
                    return False
            
            return True
            
    except Exception as e:
        print(f"✗ API tests failed: {e}")
        return False


async def test_api_data_operations():
    """Test creating and retrieving data through API."""
    base_url = get_api_base_url()
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            print("\nTesting API data operations...")
            
            # Test creating a contact
            contact_data = {
                "name": "Test User",
                "email": "test@example.com",
                "subject": "Deployment Test",
                "message": "This is a test message from the deployment verification script."
            }
            
            async with session.post(
                f"{base_url}/api/v1/contacts",
                json=contact_data
            ) as response:
                if response.status == 201:
                    contact = await response.json()
                    print(f"✓ Contact created: ID {contact.get('id')}")
                    
                    # Test retrieving contacts
                    async with session.get(f"{base_url}/api/v1/contacts") as get_response:
                        if get_response.status == 200:
                            contacts = await get_response.json()
                            print(f"✓ Retrieved {len(contacts)} contacts")
                            return True
                        else:
                            print(f"✗ Failed to retrieve contacts: {get_response.status}")
                            return False
                else:
                    print(f"✗ Failed to create contact: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"✗ API data operations test failed: {e}")
        return False


def test_environment_variables():
    """Test that all required environment variables are set."""
    print("Testing environment variables...")
    
    required_vars = [
        'POSTGRES_HOST',
        'POSTGRES_PORT', 
        'POSTGRES_USER',
        'POSTGRES_DB'
    ]
    
    optional_vars = [
        'POSTGRES_PASSWORD',
        'API_BASE_URL',
        'DATABASE_URL'
    ]
    
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: Not set (required)")
            all_good = False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            # Mask password in output
            if 'PASSWORD' in var or 'DATABASE_URL' in var:
                print(f"✓ {var}: [MASKED]")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"- {var}: Not set (optional)")
    
    return all_good


async def main():
    """Main verification function."""
    print("=" * 60)
    print("Foundation Backend Deployment Verification")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: Environment variables
    if not test_environment_variables():
        print("\n❌ Environment variables test failed")
        all_tests_passed = False
    else:
        print("\n✅ Environment variables test passed")
    
    # Test 2: Database connection and tables
    if not test_database_connection():
        print("\n❌ Database test failed")
        all_tests_passed = False
    else:
        print("\n✅ Database test passed")
    
    # Test 3: API endpoints
    if not await test_api_endpoints():
        print("\n❌ API endpoints test failed")
        all_tests_passed = False
    else:
        print("\n✅ API endpoints test passed")
    
    # Test 4: API data operations
    if not await test_api_data_operations():
        print("\n❌ API data operations test failed")
        all_tests_passed = False
    else:
        print("\n✅ API data operations test passed")
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED - Deployment verification successful!")
        print("Your Foundation Backend is ready for production use.")
    else:
        print("❌ SOME TESTS FAILED - Please check the issues above.")
        print("Your Foundation Backend may not be fully operational.")
    print("=" * 60)
    
    return 0 if all_tests_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
