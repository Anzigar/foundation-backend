#!/bin/bash

echo "🔧 Database Schema Fix Script"
echo "============================="

# Function to run SQL commands in the container
run_sql() {
    docker-compose exec -T backend python -c "
import asyncio
from sqlalchemy import text
from shared.database import async_session

async def run_query():
    async with async_session() as session:
        try:
            result = await session.execute(text('$1'))
            await session.commit()
            if result.rowcount is not None:
                print(f'✅ Query executed, {result.rowcount} rows affected')
            else:
                print('✅ Query executed successfully')
            return True
        except Exception as e:
            print(f'❌ Error: {e}')
            return False

result = asyncio.run(run_query())
exit(0 if result else 1)
"
}

# Function to check if column exists
check_column() {
    docker-compose exec -T backend python -c "
import asyncio
from sqlalchemy import text
from shared.database import async_session

async def check():
    async with async_session() as session:
        result = await session.execute(text(\"\"\"
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'project_images' AND column_name = '$1'
        \"\"\"))
        exists = result.fetchone() is not None
        print(f'Column $1 exists: {exists}')
        return exists

asyncio.run(check())
"
}

echo "📊 Checking current database schema..."

# Check if project_images table exists
echo "Checking if project_images table exists..."
docker-compose exec -T backend python -c "
import asyncio
from sqlalchemy import text
from shared.database import async_session

async def check_table():
    async with async_session() as session:
        result = await session.execute(text(\"\"\"
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'project_images'
        \"\"\"))
        exists = result.fetchone() is not None
        print(f'project_images table exists: {exists}')
        
        if exists:
            # Show current columns
            result = await session.execute(text(\"\"\"
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'project_images'
                ORDER BY ordinal_position
            \"\"\"))
            columns = result.fetchall()
            print('Current columns:')
            for col in columns:
                print(f'  - {col[0]} ({col[1]}, nullable: {col[2]})')
        
        return exists

asyncio.run(check_table())
"

echo ""
echo "🔨 Applying fixes..."

# Fix 1: Add missing is_primary column if it doesn't exist
echo "1. Adding missing is_primary column..."
check_column "is_primary"
if [ $? -ne 0 ]; then
    echo "Adding is_primary column..."
    run_sql "ALTER TABLE project_images ADD COLUMN is_primary BOOLEAN DEFAULT FALSE"
else
    echo "✅ is_primary column already exists"
fi

# Fix 2: Add missing order_index column if it doesn't exist  
echo "2. Adding missing order_index column..."
check_column "order_index"
if [ $? -ne 0 ]; then
    echo "Adding order_index column..."
    run_sql "ALTER TABLE project_images ADD COLUMN order_index INTEGER DEFAULT 0"
else
    echo "✅ order_index column already exists"
fi

# Fix 3: Update any existing data to have proper defaults
echo "3. Setting default values for existing records..."
run_sql "UPDATE project_images SET is_primary = FALSE WHERE is_primary IS NULL"
run_sql "UPDATE project_images SET order_index = 0 WHERE order_index IS NULL"

echo ""
echo "🔍 Verifying fixes..."

# Test the projects query that was failing
echo "Testing projects query..."
docker-compose exec -T backend python -c "
import asyncio
from sqlalchemy import text
from shared.database import async_session

async def test_query():
    async with async_session() as session:
        try:
            result = await session.execute(text(\"\"\"
                SELECT COUNT(*) as count
                FROM projects p
                LEFT JOIN project_images i ON p.id = i.project_id AND i.is_primary = true
                WHERE p.public = true
            \"\"\"))
            count = result.scalar()
            print(f'✅ Projects query successful: {count} projects found')
            return True
        except Exception as e:
            print(f'❌ Projects query failed: {e}')
            return False

asyncio.run(test_query())
"

# Test UUID insertion 
echo "Testing UUID handling..."
docker-compose exec -T backend python -c "
import asyncio
import uuid
from sqlalchemy import text
from shared.database import async_session

async def test_uuid():
    async with async_session() as session:
        try:
            test_id = str(uuid.uuid4())
            result = await session.execute(text(\"\"\"
                SELECT :test_id::uuid as test_uuid
            \"\"\"), {'test_id': test_id})
            uuid_result = result.scalar()
            print(f'✅ UUID handling working: {uuid_result}')
            return True
        except Exception as e:
            print(f'❌ UUID handling failed: {e}')
            return False

asyncio.run(test_uuid())
"

echo ""
echo "🎉 Database fixes completed!"
echo "You should now restart the backend service:"
echo "docker-compose restart backend"
