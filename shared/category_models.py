"""Shared category models for all content types."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, String, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from shared.database import Base

class ContentType(enum.Enum):
    """Enum for different content types that can have categories."""
    BLOG = "blog"
    NEWS = "news"
    EVENT = "event"
    PROJECT = "project"

class Category(Base):
    """Shared category model for all content types."""
    __tablename__ = "categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    content_type = Column(Enum(ContentType), nullable=False, index=True)
    color = Column(String(7))  # Hex color code for UI
    icon = Column(String(50))  # Icon name or class
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Composite unique constraint for name + content_type
    __table_args__ = (
        {'extend_existing': True},
    )

    def __repr__(self):
        return f"<Category(name='{self.name}', content_type='{self.content_type.value}')>"
