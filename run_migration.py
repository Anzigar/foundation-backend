#!/usr/bin/env python3
"""
Script to run the standardize_models.sql migration
"""
import asyncio
import asyncpg
from pathlib import Path
from config import settings

async def run_migration():
    """Run the SQL migration file."""
    try:
        # Read the migration file synchronously (file I/O is not the bottleneck here)
        migration_file = Path('migrations/standardize_models.sql')
        migration_sql = migration_file.read_text()
        
        # Connect to database
        print(f"Connecting to database: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT
        )
        
        print("Connected successfully!")
        
        # First, let's check the current schema for projects table
        print("\nChecking current projects table schema...")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'projects' 
            ORDER BY ordinal_position
        """)
        
        print("Current projects table columns:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # Execute the migration
        print("Running migration...")
        await conn.execute(migration_sql)
        
        print("Migration completed successfully!")
        
        # Close connection
        await conn.close()
        print("Database connection closed.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())
