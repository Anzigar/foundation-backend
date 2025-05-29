from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from shared.database import Base

class Contact(Base):
    """Contact form submission model."""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, index=True)
    phoneNumber = Column(String(12), nullable=True)
    subject = Column(String(255))
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    responded = Column(Boolean, default=False, index=True)
    responded_at = Column(DateTime, nullable=True)
    responded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    responder = relationship("User", back_populates="contacts_responded")

class NewsletterSubscriber(Base):
    """Newsletter subscriber model."""
    __tablename__ = "newsletter_subscribers"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100))
    subscribed_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True, index=True)
    source = Column(String(50))
