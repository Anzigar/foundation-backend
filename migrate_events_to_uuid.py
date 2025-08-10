#!/usr/bin/env python3
"""
Manual migration script to convert events uid from integer to UUID
"""
import asyncio
import asyncpg
import os
from config import DATABASE_URL

async def run_migration():
    # Connect to the database
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("Starting migration: Converting events uid from integer to UUID...")
        
        # First, add the UUID extension if not exists
        print("1. Creating UUID extension...")
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        
        # Add a new UUID column
        print("2. Adding new UUID column...")
        await conn.execute('ALTER TABLE events ADD COLUMN uid_new UUID')
        
        # Generate UUIDs for existing records
        print("3. Generating UUIDs for existing records...")
        await conn.execute('UPDATE events SET uid_new = uuid_generate_v4()')
        
        # Drop the old primary key constraint and index
        print("4. Dropping old constraints...")
        await conn.execute('ALTER TABLE events DROP CONSTRAINT IF EXISTS events_pkey')
        await conn.execute('DROP INDEX IF EXISTS ix_events_uid')
        
        # Drop the old uid column
        print("5. Dropping old uid column...")
        await conn.execute('ALTER TABLE events DROP COLUMN uid')
        
        # Rename the new column to uid
        print("6. Renaming new column...")
        await conn.execute('ALTER TABLE events RENAME COLUMN uid_new TO uid')
        
        # Make the new uid column NOT NULL
        print("7. Setting NOT NULL constraint...")
        await conn.execute('ALTER TABLE events ALTER COLUMN uid SET NOT NULL')
        
        # Create new primary key and index
        print("8. Creating new primary key and index...")
        await conn.execute('ALTER TABLE events ADD PRIMARY KEY (uid)')
        await conn.execute('CREATE INDEX ix_events_uid ON events (uid)')
        
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
