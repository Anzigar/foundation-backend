from datetime import datetime
import uuid
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from shared.database import Base

# Note: NewsCategory is removed - use shared.category_models.Category with content_type='news'

class NewsArticle(Base):
    """News article model aligned with the actual database schema."""
    __tablename__ = "news_articles"
    
    # Primary key and identifiers
    uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    
    # Content fields
    content = Column(Text, nullable=False)
    excerpt = Column(String(500))
    image_url = Column(String(255))
    source = Column(String(255))
    tags = Column(String(255))  # Database has this as varchar(255), not JSON
    
    # Publishing status
    published = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)  # Database has both fields
    featured = Column(Boolean, default=False)
    allow_comments = Column(Boolean, default=True)
    
    # SEO fields
    seo_title = Column(String(255))
    meta_description = Column(String(255))
    og_image_url = Column(String(255))
    
    # Additional content fields from database
    contact_info = Column(Text)
    author_name = Column(String(100))
    category = Column(String(100))
    
    # Event-related fields (this table seems to handle both news and events)
    venue = Column(String(255))
    location = Column(String(255))
    registration_link = Column(String(255))
    ticket_price = Column(String(100))
    event_start_date = Column(DateTime)
    event_end_date = Column(DateTime)
    
    # Timestamps
    published_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # JSON relationships (using JSONB as in database)
    category_ids = Column(JSONB, default=list)
    related_news_ids = Column(JSONB, default=list)
    
    # Table options
    __table_args__ = {'extend_existing': True}
