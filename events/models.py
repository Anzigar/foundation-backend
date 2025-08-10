from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from shared.database import Base

# Note: EventCategory is removed - use shared.category_models.Category with content_type='event'

class Event(Base):
    """Enhanced event model with comprehensive content components."""
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    excerpt = Column(String(500))
    location = Column(String(255))
    venue_details = Column(Text)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime)
    image_url = Column(String(255), CheckConstraint("image_url ~ '^https?://'"))
    ticket_price = Column(String(100))
    registration_link = Column(String(255), CheckConstraint("registration_link ~ '^https?://'"))
    contact_info = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
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
    tags = Column(JSON, default=list)  # Standardized as JSON array
    
    # Relationships as JSON (simplified)
    category_ids = Column(JSON, default=list)
    related_events = Column(JSON, default=list)
    
    # Table constraints to prevent duplicate deployments
    __table_args__ = (
        UniqueConstraint('title', 'is_deployed', name='uq_event_title_deployed'),
        UniqueConstraint('title', 'start_date', name='uq_event_title_date'),
        {'extend_existing': True}
    )
