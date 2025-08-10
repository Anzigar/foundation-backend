from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from shared.database import Base

class Contact(Base):
    """Contact form submission model."""
    __tablename__ = "contacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    full_name = Column(String(100), nullable=False)  # Updated field name
    email = Column(String(100), nullable=False, index=True)
    phone_number = Column(String(20), nullable=True)  # Updated field name
    subject = Column(String(255))
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    responded = Column(Boolean, default=False, index=True)
    responded_at = Column(DateTime, nullable=True)
    responded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    responder = relationship("User", back_populates="contacts_responded")

class NewsletterSubscriber(Base):
    """Newsletter subscriber model."""
    __tablename__ = "newsletter_subscribers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100))
    source = Column(String(50), default="Website")  # Source of subscription
    subscribed_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True, index=True)
