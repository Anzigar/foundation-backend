# Development Guide

This guide provides instructions for developers working on the Foundation Backend API.

## Development Environment Setup

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-organization/foundation-backend.git
   cd foundation-backend
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Copy `.env.example` to `.env` and adjust values as needed:
   ```bash
   cp .env.example .env
   ```

5. **Start MySQL using Docker**
   ```bash
   docker-compose -f docker-compose-local.yml up -d
   ```

6. **Run the application**
   ```bash
   uvicorn src.main:app --reload
   ```

### Docker Setup

For development with Docker:

```bash
docker-compose -f docker-compose-local.yml up -d
docker-compose build foundation-api
docker-compose up foundation-api
```

## Project Structure

```
foundation-backend/
├── database/                # Database initialization and migration files
├── src/                     # Application source code
│   ├── news/                # News module
│   │   ├── models.py        # Database models
│   │   ├── router.py        # API routes
│   │   └── schemas.py       # Pydantic schemas
│   ├── events/              # Events module
│   │   ├── models.py        # Database models
│   │   ├── router.py        # API routes
│   │   └── schemas.py       # Pydantic schemas
│   ├── contacts/            # Contacts module
│   │   ├── models.py        # Database models
│   │   ├── router.py        # API routes
│   │   └── schemas.py       # Pydantic schemas
│   └── shared/              # Shared utilities and database handling
│       ├── database.py      # Database connection and utilities
│       ├── models.py        # Shared database models
│       └── utils.py         # Utility functions
├── docs/                    # Documentation
├── tests/                   # Test cases
```

## Code Style and Standards

### Python Style Guide

- Follow the [PEP 8](https://pep8.org/) style guide
- Use 4 spaces for indentation
- Maximum line length: 88 characters (Black default)
- Use snake_case for functions and variable names
- Use PascalCase for class names
- Use UPPER_CASE for constants

### Tools

- **Black**: Code formatter
- **Flake8**: Linter
- **isort**: Import sorter

To run all linting checks:

```bash
# Format imports
isort src/

# Format code
black src/

# Check for errors
flake8 src/
```

## Database Management

### Model Creation

All database models are defined using SQLAlchemy ORM in the `models.py` files within each module. 

Example of a model:

```python
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.shared.database import Base

class MyModel(Base):
    __tablename__ = "my_table"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())
```

### Database Migrations

We use Alembic for database migrations:

```bash
# Generate a migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

## API Development

### Adding a New Endpoint

1. Define Pydantic schema in the module's `schemas.py`
2. Add the route handler in the module's `router.py`
3. Add the router to the main application in `src/main.py`

Example of a route:

```python
@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    item = await fetch_one("SELECT * FROM items WHERE id = %s", (item_id,))
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return item
```

### Error Handling

Use FastAPI's `HTTPException` for returning proper error responses:

```python
from fastapi import HTTPException

if not user:
    raise HTTPException(status_code=404, detail="User not found")
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_news.py

# Run with coverage report
pytest --cov=src
```

### Writing Tests

Place tests in the `tests/` directory, mirroring the structure of the `src/` directory.

Example test:

```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Foundation API"}
```

## Deployment

### Production Setup

1. Configure production environment variables
2. Build the Docker image:
   ```bash
   docker-compose build
   ```

3. Deploy with Docker Compose:
   ```bash
   docker-compose up -d
   ```

### CI/CD Pipeline

The project uses GitHub Actions for CI/CD. The pipeline:
1. Runs linting checks
2. Runs tests
3. Builds Docker image
4. Deploys to staging/production environments

## Troubleshooting

### Common Issues

1. **Database connection issues**:
   - Check that MySQL is running: `docker-compose -f docker-compose-local.yml ps`
   - Verify connection parameters in `.env`

2. **CORS errors**:
   - Check the CORS settings in `main.py`
   - Ensure the client origin is in the allowed origins list

3. **Docker networking issues**:
   - Ensure the `proxy` network exists: `docker network ls`
   - Create it if needed: `docker network create proxy`
