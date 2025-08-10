#!/bin/bash

echo "🔧 Fixing Foundation Backend Database Schema"
echo "=========================================="

# Navigate to the app directory inside container
cd /app

echo "📊 Current database schema status:"
echo "Checking project_images table..."

# Check if project_images table exists and its structure
python -c "
import asyncio
import sqlalchemy as sa
from sqlalchemy import text
from shared.database import async_session

async def check_schema():
    async with async_session() as session:
        try:
            # Check if project_images table exists
            result = await session.execute(text('''
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'project_images'
            '''))
            table_exists = result.fetchone() is not None
            print(f'project_images table exists: {table_exists}')
            
            if table_exists:
                # Check columns in project_images table
                result = await session.execute(text('''
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'project_images'
                    ORDER BY ordinal_position
                '''))
                columns = result.fetchall()
                print('Existing columns:')
                for col in columns:
                    print(f'  - {col[0]} ({col[1]})')
                
                # Check specifically for is_primary column
                result = await session.execute(text('''
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'project_images' AND column_name = 'is_primary'
                '''))
                has_is_primary = result.fetchone() is not None
                print(f'is_primary column exists: {has_is_primary}')
            
        except Exception as e:
            print(f'Error checking schema: {e}')

asyncio.run(check_schema())
"

echo ""
echo "🔨 Applying database schema fixes..."

# Run the migration to add missing columns
echo "Running Alembic migration..."
alembic upgrade head

echo ""
echo "✅ Database schema fix completed!"

# Verify the fix
echo "🔍 Verifying schema after migration:"
python -c "
import asyncio
import sqlalchemy as sa
from sqlalchemy import text
from shared.database import async_session

async def verify_schema():
    async with async_session() as session:
        try:
            # Check if is_primary column now exists
            result = await session.execute(text('''
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'project_images' AND column_name = 'is_primary'
            '''))
            has_is_primary = result.fetchone() is not None
            print(f'✅ is_primary column exists: {has_is_primary}')
            
            # Test the projects query
            result = await session.execute(text('''
                SELECT COUNT(*) FROM projects p
                LEFT JOIN project_images i ON p.id = i.project_id AND i.is_primary = true
                WHERE p.public = true
                LIMIT 1
            '''))
            count = result.scalar()
            print(f'✅ Projects query test successful, found {count} projects')
            
        except Exception as e:
            print(f'❌ Verification failed: {e}')

asyncio.run(verify_schema())
"

echo ""
echo "🎉 Database schema fix complete!"
echo "The Projects API should now work correctly."
