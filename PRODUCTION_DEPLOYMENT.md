# Foundation Backend Production Deployment Guide

## Overview
This guide provides comprehensive instructions for deploying the Foundation Backend to production using Docker, PostgreSQL, and Traefik with HTTPS/SSL certificates.

## Quick Deployment Summary

### Prerequisites
- AWS EC2 instance (or any Linux server)
- Docker and Docker Compose installed
- Domain name pointed to your server IP
- Ports 80 and 443 open in security groups

### 1. Environment Setup

Create a `.env` file with your production settings:

```bash
# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=foundation_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=foundation

# Async Database URL (for FastAPI)
DATABASE_URL=postgresql+asyncpg://foundation_user:your_secure_password_here@postgres:5432/foundation

# Sync Database URL (for Alembic migrations)
SQLALCHEMY_DATABASE_URL=postgresql://foundation_user:your_secure_password_here@postgres:5432/foundation

# Application Settings
ENVIRONMENT=production
DEBUG=false
PORT=8000

# Domain Configuration (replace with your domain)
DOMAIN=api.yourdomain.com
```

### 2. Deploy with Docker Compose

```bash
# Pull latest code
git pull origin main

# Build and start services
docker-compose up -d

# Check container status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Verify Deployment

Run the verification script to ensure everything is working:

```bash
# Set your API URL
export API_BASE_URL=https://api.yourdomain.com

# Run verification
python verify_deployment.py
```

## Detailed Deployment Steps

### Step 1: Server Setup

1. **Launch EC2 Instance**
   - Use Ubuntu 22.04 LTS
   - t3.small or larger recommended
   - Configure security groups for ports 22, 80, 443

2. **Install Docker**
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

3. **Configure DNS**
   - Point your domain to the server IP
   - Verify with: `dig api.yourdomain.com`

### Step 2: Application Deployment

1. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/foundation-backend.git
   cd foundation-backend
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   nano .env
   ```

3. **Set File Permissions**
   ```bash
   # Make scripts executable
   chmod +x entrypoint.sh
   chmod +x run-service.sh
   
   # Set Traefik acme.json permissions
   touch acme.json
   chmod 600 acme.json
   ```

4. **Deploy Services**
   ```bash
   # Start all services
   docker-compose up -d
   
   # Monitor logs
   docker-compose logs -f api
   docker-compose logs -f traefik
   ```

### Step 3: Database Setup

The application automatically handles database setup, but you can also run manual setup:

```bash
# Run comprehensive database setup
docker-compose exec api python setup_database.py

# Or apply manual SQL script if needed
docker-compose exec postgres psql -U foundation_user -d foundation -f /database_schema.sql
```

### Step 4: SSL Certificate Setup

Traefik automatically obtains Let's Encrypt certificates. Monitor the process:

```bash
# Check Traefik logs for certificate generation
docker-compose logs -f traefik | grep -i "certificate"

# Verify certificate status
curl -I https://api.yourdomain.com
```

### Step 5: Verification

1. **Run Automated Tests**
   ```bash
   # Install verification dependencies (if running outside container)
   pip install aiohttp

   # Set environment and run verification
   export API_BASE_URL=https://api.yourdomain.com
   export POSTGRES_HOST=localhost  # Use your server IP if running remotely
   export POSTGRES_PORT=5432
   export POSTGRES_USER=foundation_user
   export POSTGRES_PASSWORD=your_secure_password_here
   export POSTGRES_DB=foundation
   
   python verify_deployment.py
   ```

2. **Manual Verification**
   ```bash
   # Test API endpoints
   curl https://api.yourdomain.com/health
   curl https://api.yourdomain.com/docs
   curl https://api.yourdomain.com/api/v1/blog/posts
   ```

## Database Management

### Running Migrations

```bash
# Enter the API container
docker-compose exec api bash

# Run Alembic migrations
alembic upgrade head

# Check migration status
alembic current
alembic history
```

### Creating New Migrations

```bash
# Generate new migration after model changes
docker-compose exec api alembic revision --autogenerate -m "Your migration message"

# Apply the new migration
docker-compose exec api alembic upgrade head
```

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U foundation_user foundation > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose exec -T postgres psql -U foundation_user foundation < backup_file.sql
```

## Monitoring and Maintenance

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f traefik
```

### Health Checks

```bash
# Check container health
docker-compose ps

# Check API health endpoint
curl https://api.yourdomain.com/health

# Check database connection
docker-compose exec api python -c "
from shared.database import get_async_session
import asyncio
async def test(): 
    async with get_async_session() as session:
        print('Database connection successful!')
asyncio.run(test())
"
```

### Performance Monitoring

```bash
# Resource usage
docker stats

# Database performance
docker-compose exec postgres psql -U foundation_user foundation -c "
SELECT schemaname,tablename,attname,n_distinct,correlation 
FROM pg_stats 
WHERE schemaname = 'public';
"
```

## Troubleshooting

### Common Issues

1. **Traefik Certificate Issues**
   ```bash
   # Check DNS resolution
   dig api.yourdomain.com
   
   # Restart Traefik
   docker-compose restart traefik
   
   # Clear acme.json and retry
   docker-compose down
   rm acme.json && touch acme.json && chmod 600 acme.json
   docker-compose up -d
   ```

2. **Database Connection Issues**
   ```bash
   # Check PostgreSQL logs
   docker-compose logs postgres
   
   # Test database connection
   docker-compose exec postgres psql -U foundation_user foundation -c "SELECT 1;"
   ```

3. **API Not Responding**
   ```bash
   # Check API logs
   docker-compose logs api
   
   # Restart API container
   docker-compose restart api
   
   # Check port binding
   netstat -tlnp | grep 8000
   ```

### Recovery Procedures

1. **Complete Reset**
   ```bash
   # Stop all services
   docker-compose down -v
   
   # Remove all data (WARNING: This deletes all data!)
   docker system prune -a
   
   # Redeploy
   docker-compose up -d
   ```

2. **Database Recovery**
   ```bash
   # Stop API to prevent connections
   docker-compose stop api
   
   # Restore from backup
   docker-compose exec -T postgres psql -U foundation_user foundation < backup_file.sql
   
   # Restart API
   docker-compose start api
   ```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files to version control
2. **Database Password**: Use strong, unique passwords
3. **SSL/TLS**: Always use HTTPS in production
4. **Firewall**: Only open necessary ports (22, 80, 443)
5. **Updates**: Regularly update Docker images and dependencies

## Frontend Integration

Once the backend is deployed and verified, your frontend can consume the API:

- **API Base URL**: `https://api.yourdomain.com`
- **Documentation**: `https://api.yourdomain.com/docs`
- **OpenAPI Schema**: `https://api.yourdomain.com/openapi.json`

### CORS Configuration

The API is configured to accept requests from any origin in production. For tighter security, update the CORS origins in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Support and Maintenance

For ongoing support:
1. Monitor logs regularly
2. Set up automated backups
3. Keep dependencies updated
4. Monitor SSL certificate expiry
5. Run verification script periodically

Your Foundation Backend is now production-ready and can serve your frontend applications!
