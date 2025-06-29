#!/bin/bash
set -e

# Validate required environment variables
required_vars=("POSTGRES_HOST" "POSTGRES_PORT" "POSTGRES_USER" "POSTGRES_DB")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: Required environment variable $var is not set"
        exit 1
    fi
done

# Set DATABASE_URL from environment variables (handling both with and without password)
if [ -n "${POSTGRES_PASSWORD}" ]; then
    export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
else
    export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
fi

# Debug environment variables (without sensitive data)
echo "Environment variables:"
echo "POSTGRES_HOST: ${POSTGRES_HOST}"
echo "POSTGRES_PORT: ${POSTGRES_PORT}"
echo "POSTGRES_USER: ${POSTGRES_USER}"
echo "POSTGRES_DB: ${POSTGRES_DB}"
if [ -n "${POSTGRES_PASSWORD}" ]; then
    echo "DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:***@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
else
    echo "DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
fi

# Wait for database to be ready
wait_for_db() {
    echo "Waiting for database to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python -c "
import psycopg2
import os
try:
    if os.getenv('POSTGRES_PASSWORD'):
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=int(os.getenv('POSTGRES_PORT')),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB')
        )
    else:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=int(os.getenv('POSTGRES_PORT')),
            user=os.getenv('POSTGRES_USER'),
            database=os.getenv('POSTGRES_DB')
        )
    conn.close()
    print('Database is ready!')
    exit(0)
except Exception as e:
    print(f'Database not ready: {e}')
    exit(1)
"; then
            echo "Database is ready!"
            break
        else
            echo "Database not ready, waiting... (attempt $attempt/$max_attempts)"
            sleep 2
            attempt=$((attempt + 1))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        echo "Database failed to become ready after $max_attempts attempts"
        exit 1
    fi
}

echo "Python environment information:"
python --version
pip list | grep alembic || echo "Alembic not found"

# Wait for database to be ready
wait_for_db

echo "Running database migrations..."
if command -v alembic >/dev/null 2>&1; then
    # Set synchronous DATABASE_URL for Alembic migrations
    if [ -n "${POSTGRES_PASSWORD}" ]; then
        export SQLALCHEMY_DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
    else
        export SQLALCHEMY_DATABASE_URL="postgresql://${POSTGRES_USER}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
    fi
    alembic upgrade head
else
    echo "Alembic command not available, checking if it's installed as a package..."
    if pip list | grep -q alembic; then
        # Set synchronous DATABASE_URL for Alembic migrations
        if [ -n "${POSTGRES_PASSWORD}" ]; then
            export SQLALCHEMY_DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
        else
            export SQLALCHEMY_DATABASE_URL="postgresql://${POSTGRES_USER}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
        fi
        python -c "import alembic.config; alembic.config.main(argv=['upgrade', 'head'])" || \
        echo "Migration failed but continuing startup"
    else
        echo "Alembic package not found. Please add it to your requirements.txt"
        echo "Continuing without running migrations"
    fi
fi

echo "Running comprehensive database setup..."
if python setup_database.py; then
    echo "Database setup completed successfully!"
else
    echo "Database setup failed, but continuing startup..."
fi

echo "Starting the application..."
echo "Using port: ${PORT:-8000}"

# Execute the command passed to docker
exec "$@"
