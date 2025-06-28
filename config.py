from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional

class Settings(BaseSettings):
    """Application settings using Pydantic."""
    
    # Database configuration - PostgreSQL
    POSTGRES_USER: str = "foundation_user"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "foundation_db"
    
    # Database URL for SQLAlchemy - PostgreSQL
    DATABASE_URL: Optional[str] = None
    
    # Application settings
    DEBUG: bool
    SECRET_KEY: str
    ENVIRONMENT: str
    ALLOWED_HOSTS: str
    
    # API settings
    API_PREFIX: str
    API_VERSION: str
    
    # JWT Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int
    
    # CORS settings
    CORS_ORIGINS: str
    
    # Performance settings
    WORKERS: int
    
    # AWS S3 Settings
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_S3_BUCKET_NAME: str
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }
    
    @model_validator(mode='after')
    def construct_database_url(self):
        """Construct DATABASE_URL if not provided."""
        # Force PostgreSQL for development
        self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return self

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()

# Create the settings instance for import
settings = get_settings()

