#!/bin/bash

set -e

# Wait for database to be ready
echo "Waiting for MySQL database to be ready..."
while ! mysqladmin ping -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" --silent; do
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
