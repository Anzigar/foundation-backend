from datetime import datetime
from typing import Optional, List
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from shared.database import Base

class EventCategory(Base):
    """Event category model."""
    __tablename__ = "event_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    
    # Relationships
    events = relationship(
        "Event",
        secondary="event_categories_relation",
        back_populates="categories"
    )

class Event(Base):
    """Enhanced event model with comprehensive content components."""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)                   # Title/Headline
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)                    # Full Content/Description
    excerpt = Column(String(500))                                 # Short Summary
    location = Column(String(255))                                # Venue/Location
    venue_details = Column(Text)                                  # Additional venue info
    map_embed_url = Column(String(500))                           # Map embed
    start_date = Column(DateTime, nullable=False, index=True)     # Event start date/time
    end_date = Column(DateTime)                                   # Event end date/time
    image_url = Column(String(255))                               # Featured Image
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Organizer
    ticket_price = Column(String(100))                            # Ticket Price info
    registration_link = Column(String(255))                       # Registration Link
    rsvp_enabled = Column(Boolean, default=False)                 # RSVP Form toggle
    contact_info = Column(Text)                                   # Contact Information
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    published = Column(Boolean, default=False)
    published_at = Column(DateTime)                               # Publication date/time
    featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)                      # For Social Sharing tracking
    comment_count = Column(Integer, default=0)                    # Comment tracking
    allow_comments = Column(Boolean, default=True)                # Comments Section toggle
    seo_title = Column(String(255))                               # SEO
    meta_description = Column(String(255))                        # SEO
    og_image_url = Column(String(255))                            # Social preview image
    related_events = Column(JSON)                                 # Related News/Events links
    tags = Column(String(255))                                    # Keywords/Tags as comma-separated string
    
    # Relationships
    organizer = relationship("User", back_populates="events")
    categories = relationship(
        "EventCategory",
        secondary="event_categories_relation",
        back_populates="events"
    )
    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")
    comments = relationship("EventComment", back_populates="event", cascade="all, delete-orphan")

class EventCategoryRelation(Base):
    """Association table for events and categories."""
    __tablename__ = "event_categories_relation"
    
    event_id = Column(Integer, ForeignKey("events.id"), primary_key=True)
    category_id = Column(Integer, ForeignKey("event_categories.id"), primary_key=True)

class EventRegistration(Base):
    """Event registration model."""
    __tablename__ = "event_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, index=True)
    phone = Column(String(20))
    additional_info = Column(JSON)
    status = Column(Enum("pending", "confirmed", "canceled", name="registration_status"), default="pending", index=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    event = relationship("Event", back_populates="registrations")

class EventComment(Base):
    """Event comment model."""
    __tablename__ = "event_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("event_comments.id"), nullable=True)
    author_name = Column(String(100), nullable=False)
    author_email = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    event = relationship("Event", back_populates="comments")
    parent = relationship("EventComment", remote_side=[id], backref="replies")
