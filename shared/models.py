from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from shared.database import Base

class User(Base):
    """User model for authentication and author information."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    bio = Column(Text)
    profile_image_url = Column(String(255))
    social_links = Column(JSON)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    news_articles = relationship("NewsArticle", back_populates="author")
    events = relationship("Event", back_populates="organizer")
    contacts_responded = relationship("Contact", back_populates="responder")
    blog_posts = relationship("BlogPost", back_populates="author")
