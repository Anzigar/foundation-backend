from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from shared.database import Base

class BlogPost(Base):
    __tablename__ = "blog_posts"

    uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    introduction = Column(Text)
    image_url = Column(String(255), CheckConstraint("image_url ~ '^https?://'"))
    author_name = Column(String(100))
    author_bio = Column(Text)
    cta_text = Column(String(100))
    cta_link = Column(String(255), CheckConstraint("cta_link ~ '^https?://'"))
    # Remove tag duplication - use only JSON array for tags
    tags = Column(JSON, default=list)  # Array of tag strings
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime)  # Timestamp when first published
    last_published_at = Column(DateTime)  # Timestamp of last publication
    deployment_count = Column(Integer, default=0)  # Track number of deployments
    is_deployed = Column(Boolean, default=False)  # Current deployment status
    deployed_at = Column(DateTime)  # When it was deployed
    featured = Column(Boolean, default=False)
    allow_comments = Column(Boolean, default=True)
    seo_title = Column(String(255))
    meta_description = Column(Text)
    # Add image URL validation
    og_image_url = Column(String(255), CheckConstraint("og_image_url ~ '^https?://'"))
    source = Column(String(255))
    contact_info = Column(Text)
    publish_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Standardize all IDs to UUIDs
    featured_image_id = Column(UUID(as_uuid=True))
    og_image_id = Column(UUID(as_uuid=True))
    related_blog_ids = Column(JSON, default=list)
    category_ids = Column(JSON, default=list)  # For managing categories via JSON array
    related_news_ids = Column(JSON, default=list)

    # Table constraints to prevent duplicate deployments
    __table_args__ = (
        UniqueConstraint('title', 'is_published', name='uq_blog_post_title_published'),
        {'extend_existing': True}
    )

# Note: BlogCategory is removed - use shared.category_models.Category with content_type='blog'
