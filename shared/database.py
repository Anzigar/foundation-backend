import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use the database URL from settings
database_url = settings.DATABASE_URL
logger.info(f"Using database URL: {database_url}")

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
    # Import all models to ensure they are registered with Base
    from blog.models import BlogPost
    from news.models import NewsArticle  
    from events.models import Event
    from projects.models import Project, ProjectImage
    from contacts.models import Contact, NewsletterSubscriber
    from shared.models import User
    from shared.category_models import Category
    from shared.image_models import ContentImage, ImageTag, ContentImageTag
    
    async with engine.begin() as conn:
        logger.info("Creating database tables if they don't exist")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created or verified")
