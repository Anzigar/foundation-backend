#!/bin/bash
set -e

# Foundation Backend Production Deployment Script
# This script automates the complete deployment process

echo "=========================================="
echo "Foundation Backend Production Deployment"
echo "=========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_status "Creating .env template..."
    cat > .env << EOF
# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=foundation_user
POSTGRES_PASSWORD=change_this_password
POSTGRES_DB=foundation

# Async Database URL (for FastAPI)
DATABASE_URL=postgresql+asyncpg://foundation_user:change_this_password@postgres:5432/foundation

# Sync Database URL (for Alembic migrations)
SQLALCHEMY_DATABASE_URL=postgresql://foundation_user:change_this_password@postgres:5432/foundation

# Application Settings
ENVIRONMENT=production
DEBUG=false
PORT=8000

# Domain Configuration (replace with your domain)
DOMAIN=api.yourdomain.com
EOF
    print_warning ".env file created with template values"
    print_warning "Please edit .env with your actual configuration before continuing"
    print_status "Run: nano .env"
    exit 1
fi

print_success ".env file found"

# Source environment variables
source .env

# Validate required environment variables
required_vars=("POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB" "DOMAIN")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Required environment variable $var is not set in .env"
        exit 1
    fi
done

print_success "Environment variables validated"

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running"
    exit 1
fi

print_success "Docker is available"

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed"
    exit 1
fi

print_success "Docker Compose is available"

# Set correct permissions
print_status "Setting file permissions..."
chmod +x entrypoint.sh
chmod +x run-service.sh
touch acme.json
chmod 600 acme.json
print_success "File permissions set"

# Build and start services
print_status "Building and starting services..."
docker-compose down --remove-orphans
docker-compose build --no-cache
docker-compose up -d

print_success "Services started"

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Check service status
print_status "Checking service status..."
if ! docker-compose ps | grep -q "Up"; then
    print_error "Some services failed to start"
    print_status "Service status:"
    docker-compose ps
    print_status "Logs:"
    docker-compose logs --tail=20
    exit 1
fi

print_success "All services are running"

# Wait a bit more for database initialization
print_status "Waiting for database initialization..."
sleep 15

# Run database setup
print_status "Running database setup..."
if docker-compose exec -T api python setup_database.py; then
    print_success "Database setup completed"
else
    print_warning "Database setup had issues, but continuing..."
fi

# Test API endpoints
print_status "Testing API endpoints..."
API_URL="http://localhost:8000"

# Test health endpoint
if curl -f -s "$API_URL/health" > /dev/null; then
    print_success "Health endpoint is responding"
else
    print_error "Health endpoint is not responding"
    print_status "API logs:"
    docker-compose logs --tail=10 api
fi

# Test root endpoint
if curl -f -s "$API_URL/" > /dev/null; then
    print_success "Root endpoint is responding"
else
    print_warning "Root endpoint is not responding"
fi

# Test docs endpoint
if curl -f -s "$API_URL/docs" > /dev/null; then
    print_success "Documentation is accessible"
else
    print_warning "Documentation is not accessible"
fi

# Display service URLs
print_status "Deployment Summary:"
echo "=========================="
echo "API URL (HTTP): http://localhost:8000"
echo "API Health: http://localhost:8000/health"
echo "API Docs: http://localhost:8000/docs"
echo "Traefik Dashboard: http://localhost:8080"
if [ "$DOMAIN" != "api.yourdomain.com" ]; then
    echo "Production URL: https://$DOMAIN"
    echo "Production Health: https://$DOMAIN/health"
    echo "Production Docs: https://$DOMAIN/docs"
fi
echo "=========================="

# Display next steps
print_status "Next Steps:"
echo "1. Wait for SSL certificate generation (may take a few minutes)"
echo "2. Test your domain: curl https://$DOMAIN/health"
echo "3. Run verification script: python verify_deployment.py"
echo "4. Check logs: docker-compose logs -f"

# Optional: Run verification if the script exists and aiohttp is available
if [ -f "verify_deployment.py" ] && python -c "import aiohttp" 2>/dev/null; then
    print_status "Running deployment verification..."
    if [ "$DOMAIN" != "api.yourdomain.com" ]; then
        export API_BASE_URL="https://$DOMAIN"
    else
        export API_BASE_URL="http://localhost:8000"
    fi
    
    if python verify_deployment.py; then
        print_success "Deployment verification passed!"
    else
        print_warning "Deployment verification had issues"
    fi
else
    print_warning "Verification script not available or aiohttp not installed"
    print_status "Install aiohttp to run verification: pip install aiohttp"
fi

print_success "Deployment completed!"
print_status "Monitor with: docker-compose logs -f"
