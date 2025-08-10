#!/usr/bin/env python3
"""
Manual migration script to convert events uid from integer to UUID
"""
import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.helpers import execute_query

async def run_migration():
    try:
        print("Starting migration: Converting events uid from integer to UUID...")
        
        # First, add the UUID extension if not exists
        print("1. Creating UUID extension...")
        await execute_query('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        
        # Add a new UUID column
        print("2. Adding new UUID column...")
        await execute_query('ALTER TABLE events ADD COLUMN uid_new UUID')
        
        # Generate UUIDs for existing records
        print("3. Generating UUIDs for existing records...")
        await execute_query('UPDATE events SET uid_new = uuid_generate_v4()')
        
        # Drop the old primary key constraint and index
        print("4. Dropping old constraints...")
        await execute_query('ALTER TABLE events DROP CONSTRAINT IF EXISTS events_pkey')
        await execute_query('DROP INDEX IF EXISTS ix_events_uid')
        
        # Drop the old uid column
        print("5. Dropping old uid column...")
        await execute_query('ALTER TABLE events DROP COLUMN uid')
        
        # Rename the new column to uid
        print("6. Renaming new column...")
        await execute_query('ALTER TABLE events RENAME COLUMN uid_new TO uid')
        
        # Make the new uid column NOT NULL
        print("7. Setting NOT NULL constraint...")
        await execute_query('ALTER TABLE events ALTER COLUMN uid SET NOT NULL')
        
        # Create new primary key and index
        print("8. Creating new primary key and index...")
        await execute_query('ALTER TABLE events ADD PRIMARY KEY (uid)')
        await execute_query('CREATE INDEX ix_events_uid ON events (uid)')
        
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())
