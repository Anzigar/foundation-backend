import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Make sure we're using the async SQLite driver if using SQLite
database_url = settings.DATABASE_URL
if database_url.startswith('sqlite://') and not database_url.startswith('sqlite+aiosqlite://'):
    database_url = database_url.replace('sqlite://', 'sqlite+aiosqlite://', 1)
    logger.info(f"Modified database URL to use async SQLite driver: {database_url}")

# Create SQLAlchemy engine
engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
class Base(DeclarativeBase):
    pass

# Dependency for SQLAlchemy session
async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Function to create all tables defined in our models
async def create_tables():
    from blog.models import Base  # Import here to avoid circular imports
    
    async with engine.begin() as conn:
        logger.info("Creating database tables if they don't exist")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created or verified")
