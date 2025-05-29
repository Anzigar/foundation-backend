from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl

class BlogTagBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

class BlogTagCreate(BlogTagBase):
    pass

class BlogTagResponse(BlogTagBase):
    id: int

class AuthorInfo(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None

class BlogPostBase(BaseModel):
    title: str
    introduction: Optional[str] = None
    content: str
    excerpt: Optional[str] = None
    featured_image_url: Optional[str] = None
    cta_text: Optional[str] = None
    cta_link: Optional[str] = None
    allow_comments: bool = True
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None
    newsletter_form_enabled: bool = False
    published: bool = False

class BlogPostCreate(BlogPostBase):
    slug: Optional[str] = None  # Will be generated if not provided
    tag_ids: List[int] = []
    related_post_ids: List[int] = []

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    introduction: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    featured_image_url: Optional[str] = None
    cta_text: Optional[str] = None
    cta_link: Optional[str] = None
    allow_comments: Optional[bool] = None
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None
    newsletter_form_enabled: Optional[bool] = None
    published: Optional[bool] = None
    tag_ids: Optional[List[int]] = None
    related_post_ids: Optional[List[int]] = None

class BlogPostResponse(BlogPostBase):
    id: int
    slug: str
    author: AuthorInfo
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    view_count: int
    share_count: int
    comment_count: int
    tags: List[BlogTagResponse] = []
    related_posts: List[Dict[str, Any]] = []  # Simplified related posts data

class BlogPostListItem(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: Optional[str]
    featured_image_url: Optional[str]
    author: AuthorInfo
    published_at: Optional[datetime]
    created_at: datetime
    tags: List[BlogTagResponse] = []
    view_count: int
    comment_count: int

class BlogCommentBase(BaseModel):
    author_name: str
    author_email: str
    content: str
    parent_id: Optional[int] = None

class BlogCommentCreate(BlogCommentBase):
    pass

class BlogCommentResponse(BlogCommentBase):
    id: int
    post_id: int
    is_approved: bool
    created_at: datetime
    replies: Optional[List["BlogCommentResponse"]] = []

# Update the User model in shared/models.py to include blog_posts relationship
# Add this to the User class in shared/models.py:
# blog_posts = relationship("BlogPost", back_populates="author")
