#!/bin/bash

set -e

# Wait for database to be ready
echo "Waiting for PostgreSQL database to be ready..."
until python -c "
import psycopg2
import os
import sys
try:
    # Try with password first (production), then without (local)
    password = os.getenv('POSTGRES_PASSWORD')
    if password:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'database'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER'),
            password=password,
            database=os.getenv('POSTGRES_DB')
        )
    else:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'database'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER'),
            database=os.getenv('POSTGRES_DB')
        )
    conn.close()
    print('Database connection successful!')
    sys.exit(0)
except Exception as e:
    print(f'Database not ready: {e}')
    sys.exit(1)
" 2>/dev/null; do
    echo "Database not ready yet, waiting..."
    sleep 2
done

echo "Database is ready!"

# Run database migrations
echo "Running database migrations..."
# If you're using Alembic for migrations, uncomment the following line:
# alembic upgrade head

# Create database tables if they don't exist
echo "Ensuring database tables exist..."
python -c "
import os
from sqlalchemy import create_engine
from shared.database import Base

# Create synchronous engine for table creation
password = os.getenv('POSTGRES_PASSWORD')
if password:
    sync_db_url = f'postgresql://{os.getenv(\"POSTGRES_USER\")}:{password}@{os.getenv(\"POSTGRES_HOST\")}:{os.getenv(\"POSTGRES_PORT\")}/{os.getenv(\"POSTGRES_DB\")}'
else:
    sync_db_url = f'postgresql://{os.getenv(\"POSTGRES_USER\")}@{os.getenv(\"POSTGRES_HOST\")}:{os.getenv(\"POSTGRES_PORT\")}/{os.getenv(\"POSTGRES_DB\")}'
sync_engine = create_engine(sync_db_url)
Base.metadata.create_all(bind=sync_engine)
print('Database tables created successfully!')
"

# Execute the command passed to docker
exec "$@"
