#!/usr/bin/env python3
"""
Set default UUID generator for events table
"""
import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.helpers import execute_query

async def set_events_uuid_default():
    try:
        print("Setting default UUID generator for events table...")
        
        # Ensure UUID extension exists
        print("1. Ensuring UUID extension exists...")
        await execute_query('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        
        # Set default UUID generator for uid column
        print("2. Setting default UUID generator for uid column...")
        await execute_query('ALTER TABLE events ALTER COLUMN uid SET DEFAULT uuid_generate_v4()')
        
        print("✅ Default UUID generator set successfully!")
        
    except Exception as e:
        print(f"❌ Failed to set default UUID generator: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(set_events_uuid_default())
