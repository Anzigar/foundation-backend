from datetime import datetime
from typing import Optional, List
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from shared.database import Base

class NewsCategory(Base):
    """News category model."""
    __tablename__ = "news_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    
    # Relationships
    articles = relationship(
        "NewsArticle",
        secondary="news_article_categories",
        back_populates="categories"
    )

class NewsArticle(Base):
    """Enhanced news article model with comprehensive content components."""
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)                    # Title/Headline
    slug = Column(String(255), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)                         # Full Content
    excerpt = Column(String(500))                                  # Short Summary
    image_url = Column(String(255))                                # Featured Image
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Author
    source = Column(String(255))                                   # Source
    published_at = Column(DateTime, default=func.now())            # Publish Date & Time
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    published = Column(Boolean, default=False)
    featured = Column(Boolean, default=False)
    contact_info = Column(Text)                                    # Contact Information
    view_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)                       # For Social Sharing tracking
    comment_count = Column(Integer, default=0)
    allow_comments = Column(Boolean, default=True)                 # Comments Section toggle
    seo_title = Column(String(255))                                # SEO
    meta_description = Column(String(255))                         # SEO
    og_image_url = Column(String(255))                             # Social preview image
    related_news = Column(JSON)                                    # Related News/Events links
    tags = Column(String(255))                                     # Keywords/Tags as comma-separated string
    
    # Relationships
    author = relationship("User", back_populates="news_articles")
    categories = relationship(
        "NewsCategory",
        secondary="news_article_categories",
        back_populates="articles"
    )
    comments = relationship("NewsComment", back_populates="article", cascade="all, delete-orphan")

class NewsArticleCategory(Base):
    """Association table for news articles and categories."""
    __tablename__ = "news_article_categories"
    
    article_id = Column(Integer, ForeignKey("news_articles.id"), primary_key=True)
    category_id = Column(Integer, ForeignKey("news_categories.id"), primary_key=True)

class NewsComment(Base):
    """News comment model."""
    __tablename__ = "news_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("news_comments.id"), nullable=True)
    author_name = Column(String(100), nullable=False)
    author_email = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    article = relationship("NewsArticle", back_populates="comments")
    parent = relationship("NewsComment", remote_side=[id], backref="replies")
