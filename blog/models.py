from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, JSON, Table
from sqlalchemy.orm import relationship

from shared.database import Base

# Association table for blog posts and tags (many-to-many)
blog_post_tags = Table(
    "blog_post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("blog_posts.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("blog_tags.id"), primary_key=True),
)

class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    introduction = Column(Text)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    featured_image_url = Column(String(255))
    cta_text = Column(String(100))
    cta_link = Column(String(255))
    allow_comments = Column(Boolean, default=True)
    seo_title = Column(String(255))
    meta_description = Column(Text)
    og_image_url = Column(String(255))
    newsletter_form_enabled = Column(Boolean, default=False)
    published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    view_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    related_posts = Column(JSON, default=list)
    
    # Foreign keys
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    tags = relationship("BlogTag", secondary=blog_post_tags, back_populates="posts")
    author = relationship("User", back_populates="blog_posts")

class BlogTag(Base):
    __tablename__ = "blog_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    
    # Relationships
    posts = relationship("BlogPost", secondary=blog_post_tags, back_populates="tags")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100))
    bio = Column(Text)
    profile_image_url = Column(String(255))
    password_hash = Column(String(255), nullable=False)
    social_links = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    blog_posts = relationship("BlogPost", back_populates="author")
