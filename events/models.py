from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.sql import func

from shared.database import Base

class EventCategory(Base):
    """Event category model."""
    __tablename__ = "event_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))

class Event(Base):
    """Enhanced event model with comprehensive content components."""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    excerpt = Column(String(500))
    location = Column(String(255))
    venue_details = Column(Text)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime)
    image_url = Column(String(255))
    ticket_price = Column(String(100))
    registration_link = Column(String(255))
    contact_info = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    published = Column(Boolean, default=False)
    featured = Column(Boolean, default=False)
    allow_comments = Column(Boolean, default=True)
    seo_title = Column(String(255))
    meta_description = Column(String(255))
    og_image_url = Column(String(255))
    tags = Column(String(255))
    
    # Relationships as JSON (simplified)
    category_ids = Column(JSON, default=list)
    related_events = Column(JSON, default=list)
