# Foundation Backend API

A FastAPI-based backend service for the Foundation website.

## Features

- News article management
- Events management
- Contact form handling
- Newsletter subscription
- Secure API endpoints with JWT authentication
- Database ORM with SQLAlchemy
- Docker containerization

## Technology Stack

- **Python 3.13+**: Core programming language
- **FastAPI**: Web framework for building APIs
- **SQLAlchemy**: ORM for database operations
- **MySQL**: Database
- **Docker**: Containerization
- **Traefik**: API Gateway and Load Balancer

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Python 3.13+ (for local development)

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/foundation-backend.git
   cd foundation-backend
   ```

2. Copy the environment example file and adjust it for your needs:
   ```bash
   cp .env.example .env
   ```

3. Modify the `.env` file with your specific configuration.

### Running with Docker (Recommended)

For local development with Docker:

```bash
docker-compose -f docker-compose-local.yml up -d
```

This will start the MySQL database service. To access the database:

- Port: 3306
- Username: from your .env file
- Password: from your .env file

For full deployment with Traefik:

```bash
docker-compose up -d
```

This starts:
- Traefik as reverse proxy
- Foundation API service
- MySQL database

### Running Locally (without Docker)

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn src.main:app --reload
   ```

## Project Structure

```
foundation-backend/
├── database/                # Database initialization and migration files
├── src/                     # Application source code
│   ├── news/                # News module
│   ├── events/              # Events module
│   ├── contacts/            # Contacts module
│   └── shared/              # Shared utilities and database handling
├── docs/                    # Documentation
├── tests/                   # Test cases
├── docker-compose.yml       # Production Docker configuration
├── docker-compose-local.yml # Local development Docker configuration
├── Dockerfile               # Docker build instructions
├── entrypoint.sh            # Docker entrypoint script
├── run-service.sh           # Service run script
└── requirements.txt         # Python dependencies
```

## Documentation

For more detailed documentation, please refer to:

- [API Documentation](./docs/api.md)
- [Development Guide](./docs/development.md)

## License

[Your License] © [Your Organization]
