#!/bin/bash

set -e

# Wait for database to be ready
echo "Waiting for PostgreSQL database to be ready..."
until python -c "
import psycopg2
import os
import sys
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
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
python -c "from shared.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Execute the command passed to docker
exec "$@"
