from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON, CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from shared.database import Base

class Project(Base):
    """Project model for showcasing foundation projects."""
    __tablename__ = "projects"
    
    uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    project_image = Column(String(255))  # Main project image URL
    project_image_preview = Column(String(255))  # Preview image URL
    image_title = Column(String(255))  # Image title
    image_description = Column(Text)  # Image description
    source_link = Column(String(255), CheckConstraint("source_link ~ '^https?://'"))  # Source/repository link (GitHub, etc.)
    live_link = Column(String(255), CheckConstraint("live_link ~ '^https?://'"))  # Live/demo link
    technologies = Column(JSON, default=list)  # Array of technologies used
    is_ongoing = Column(Boolean, default=True)  # Is project ongoing
    start_date = Column(DateTime)  # Project start date
    end_date = Column(DateTime)  # Project end date (null if ongoing)
    featured = Column(Boolean, default=False)  # Is featured project
    public = Column(Boolean, default=True)  # Is publicly visible
    
    # Deployment tracking
    is_deployed = Column(Boolean, default=False)  # Current deployment status
    deployed_at = Column(DateTime)  # When it was deployed
    deployment_count = Column(Integer, default=0)  # Track number of deployments
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    images = relationship("ProjectImage", back_populates="project", order_by="ProjectImage.order_index")
    
    # Table constraints to prevent duplicate deployments
    __table_args__ = (
        UniqueConstraint('title', 'is_deployed', name='uq_project_title_deployed'),
        {'extend_existing': True}
    )

class ProjectImage(Base):
    """Images associated with projects."""
    __tablename__ = "project_images"
    
    uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_uid = Column(UUID(as_uuid=True), ForeignKey("projects.uid"), nullable=False)  # Reference to Project.uid
    title = Column(String(255))
    description = Column(Text)
    image_url = Column(String(255), CheckConstraint("image_url ~ '^https?://'"), nullable=True)
    is_primary = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    project = relationship("Project", back_populates="images")
