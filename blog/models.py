from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship

from shared.database import Base

class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    introduction = Column(Text)
    image_url = Column(String(255))
    author_name = Column(String(100))
    author_bio = Column(Text)
    cta_text = Column(String(100))
    cta_link = Column(String(255))
    tags = Column(String(255))  # Comma-separated tags
    is_published = Column(Boolean, default=False)
    featured = Column(Boolean, default=False)
    allow_comments = Column(Boolean, default=True)
    seo_title = Column(String(255))
    meta_description = Column(Text)
    og_image_url = Column(String(255))
    source = Column(String(255))
    contact_info = Column(Text)
    publish_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships as simple IDs and JSON arrays
    category_id = Column(Integer)
    featured_image_id = Column(Integer)
    og_image_id = Column(Integer)
    tag_ids = Column(JSON, default=list)
    related_blog_ids = Column(JSON, default=list)
    category_ids = Column(JSON, default=list)  # For compatibility
    related_news_ids = Column(JSON, default=list)

class BlogCategory(Base):
    __tablename__ = "blog_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
