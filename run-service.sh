#!/bin/bash

set -e

# Default to development mode if not specified
ENVIRONMENT=${ENVIRONMENT:-development}

echo "Starting Foundation API in $ENVIRONMENT mode..."

if [ "$ENVIRONMENT" = "production" ]; then
    # Production: Run using Gunicorn with Uvicorn workers
    exec gunicorn main:app \
        --bind 0.0.0.0:8000 \
        --workers ${WORKERS:-4} \
        --worker-class uvicorn.workers.UvicornWorker \
        --access-logfile - \
        --error-logfile -
else
    # Development: Run using Uvicorn with auto-reload
    exec uvicorn main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload
fi
