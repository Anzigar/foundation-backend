from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
import uuid

from shared.database import Base

# Note: EventCategory is removed - use shared.category_models.Category with content_type='event'

class Event(Base):
    """Event model aligned with the actual database schema."""
    __tablename__ = "events"
    
    # Primary key - using UUID for security
    uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    
    # Content fields
    description = Column(Text, nullable=False)
    excerpt = Column(String(500))
    location = Column(String(255))
    venue_details = Column(Text)
    
    # Date fields (database has both start_date and event_date)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime)
    event_date = Column(DateTime)  # Additional field in database
    
    # Media and external links
    image_url = Column(String(255))
    ticket_price = Column(String(100))
    registration_link = Column(String(255))
    contact_info = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Publishing status
    published = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)  # Database has both fields
    featured = Column(Boolean, default=False)
    allow_comments = Column(Boolean, default=True)
    
    # SEO fields
    seo_title = Column(String(255))
    meta_description = Column(String(255))
    og_image_url = Column(String(255))
    
    # Additional fields from database
    tags = Column(String(255))  # Database has this as varchar(255), not JSON
    author_name = Column(String(100))
    
    # JSON relationships (using JSONB as in database)
    category_ids = Column(JSONB, default=list)
    related_events = Column(JSONB, default=list)
    
    # Table options
    __table_args__ = {'extend_existing': True}
