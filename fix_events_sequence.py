#!/usr/bin/env python3
"""
Fix events table auto-increment sequence
"""
import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.helpers import execute_query, fetch_one

async def fix_events_sequence():
    try:
        print("Fixing events table auto-increment sequence...")
        
        # Check current sequence
        print("1. Checking current sequence...")
        sequence_info = await fetch_one("SELECT * FROM information_schema.sequences WHERE sequence_name LIKE '%events%'")
        if sequence_info:
            print(f"   Found sequence: {sequence_info}")
        else:
            print("   No sequence found for events table")
        
        # Get the current max uid
        print("2. Getting current max uid...")
        max_result = await fetch_one("SELECT COALESCE(MAX(uid), 0) as max_uid FROM events")
        max_uid = max_result['max_uid'] if max_result else 0
        print(f"   Current max uid: {max_uid}")
        
        # Create or reset the sequence
        print("3. Creating/resetting sequence...")
        await execute_query("DROP SEQUENCE IF EXISTS events_uid_seq CASCADE")
        await execute_query(f"CREATE SEQUENCE events_uid_seq START {max_uid + 1}")
        
        # Set the column default to use the sequence
        print("4. Setting column default...")
        await execute_query("ALTER TABLE events ALTER COLUMN uid SET DEFAULT nextval('events_uid_seq')")
        
        # Set sequence ownership
        print("5. Setting sequence ownership...")
        await execute_query("ALTER SEQUENCE events_uid_seq OWNED BY events.uid")
        
        print("✅ Events sequence fixed successfully!")
        
    except Exception as e:
        print(f"❌ Failed to fix sequence: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(fix_events_sequence())
