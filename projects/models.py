from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from shared.database import Base

class Project(Base):
    """Project model for showcasing foundation projects."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    timeline = Column(String(255))  # Project timeline (e.g., "2023-2024", "Ongoing")
    links = Column(JSON)  # Store links as JSON (e.g., {"website": "...", "github": "..."})
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    published = Column(Boolean, default=False)
    featured = Column(Boolean, default=False)
    
    # Relationships
    images = relationship("ProjectImage", back_populates="project", cascade="all, delete-orphan")

class ProjectImage(Base):
    """Images associated with projects."""
    __tablename__ = "project_images"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255))  # Image title
    description = Column(Text)  # Image description
    image_url = Column(String(255), nullable=False)
    primary = Column(Boolean, default=False)  # Is this the primary/featured image?
    order = Column(Integer, default=0)  # For ordering images
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="images")
