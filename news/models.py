from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.sql import func

from shared.database import Base

class NewsCategory(Base):
    """News category model."""
    __tablename__ = "news_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))

class NewsArticle(Base):
    """Enhanced news article model with comprehensive content components."""
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(String(500))
    image_url = Column(String(255))
    source = Column(String(255))
    tags = Column(String(255))  # Keywords/Tags as comma-separated string
    published = Column(Boolean, default=False)
    featured = Column(Boolean, default=False)
    allow_comments = Column(Boolean, default=True)
    seo_title = Column(String(255))
    meta_description = Column(String(255))
    og_image_url = Column(String(255))
    contact_info = Column(Text)
    
    # Event-specific fields (for when this is used as an event)
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
    
    # Relationships as JSON (simplified)
    category_ids = Column(JSON, default=list)
    related_news_ids = Column(JSON, default=list)
