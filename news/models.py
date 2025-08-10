from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func

from shared.database import Base

# Note: NewsCategory is removed - use shared.category_models.Category with content_type='news'

class NewsArticle(Base):
    """News article model focused on news content only."""
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(String(500))
    image_url = Column(String(255), CheckConstraint("image_url ~ '^https?://'"))
    source = Column(String(255))
    author_name = Column(String(100))
    author_bio = Column(Text)
    tags = Column(JSON, default=list)  # Standardized as JSON array
    published = Column(Boolean, default=False)
    
    # Deployment tracking
    is_deployed = Column(Boolean, default=False)  # Current deployment status
    deployed_at = Column(DateTime)  # When it was deployed
    deployment_count = Column(Integer, default=0)  # Track number of deployments
    
    featured = Column(Boolean, default=False)
    allow_comments = Column(Boolean, default=True)
    seo_title = Column(String(255))
    meta_description = Column(String(255))
    og_image_url = Column(String(255), CheckConstraint("og_image_url ~ '^https?://'"))
    contact_info = Column(Text)
    
    # Timestamps
    published_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships as JSON (simplified)
    category_ids = Column(JSON, default=list)
    related_news_ids = Column(JSON, default=list)
    related_event_ids = Column(JSON, default=list)  # Link to related events
    
    # Table constraints to prevent duplicate deployments
    __table_args__ = (
        UniqueConstraint('title', 'is_deployed', name='uq_news_title_deployed'),
        {'extend_existing': True}
    )
