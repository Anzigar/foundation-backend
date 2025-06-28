from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.sql import func

from shared.database import Base

class Project(Base):
    """Project model for showcasing foundation projects."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    project_image = Column(String(255))  # Main project image URL
    project_image_preview = Column(String(255))  # Preview image URL
    image_title = Column(String(255))  # Image title
    image_description = Column(Text)  # Image description
    github_link = Column(String(255))  # GitHub link
    demo_link = Column(String(255))  # Demo link
    technologies = Column(JSON, default=list)  # Array of technologies
    is_ongoing = Column(Boolean, default=True)  # Is project ongoing
    start_date = Column(DateTime)  # Project start date
    end_date = Column(DateTime)  # Project end date (null if ongoing)
    featured = Column(Boolean, default=False)  # Is featured project
    public = Column(Boolean, default=True)  # Is publicly visible
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ProjectImage(Base):
    """Images associated with projects."""
    __tablename__ = "project_images"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=False)
    title = Column(String(255))
    description = Column(Text)
    image_url = Column(String(255), nullable=False)
    primary = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
