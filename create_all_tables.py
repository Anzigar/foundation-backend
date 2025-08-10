#!/usr/bin/env python3
"""
Create all database tables using SQLAlchemy.
"""

import asyncio
import os
from shared.database import engine, Base

# Import all models to ensure they're registered with Base
from blog.models import *
from news.models import *
from events.models import *
from projects.models import *
from contacts.models import *
from shared.models import *
from shared.media_models import *

async def create_tables():
    """Create all tables."""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("All tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())
