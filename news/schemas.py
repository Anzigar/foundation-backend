from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, field_serializer

class NewsArticleCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[str] = None  # Database stores as varchar(255)
    published: bool = False
    is_published: bool = False  # Database has both fields
    featured: bool = False
    allow_comments: bool = True
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None
    contact_info: Optional[str] = None
    author_name: Optional[str] = None
    category: Optional[str] = None
    
    # Event-related fields (since the table handles both news and events)
    venue: Optional[str] = None
    location: Optional[str] = None
    registration_link: Optional[str] = None
    ticket_price: Optional[str] = None
    event_start_date: Optional[datetime] = None
    event_end_date: Optional[datetime] = None
    
    # JSON fields
    category_ids: Optional[List] = []
    related_news_ids: Optional[List] = []
    
    slug: Optional[str] = None

class NewsArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[str] = None
    published: Optional[bool] = None
    is_published: Optional[bool] = None
    featured: Optional[bool] = None
    allow_comments: Optional[bool] = None
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None
    contact_info: Optional[str] = None
    author_name: Optional[str] = None
    category: Optional[str] = None
    
    # Event-related fields
    venue: Optional[str] = None
    location: Optional[str] = None
    registration_link: Optional[str] = None
    ticket_price: Optional[str] = None
    event_start_date: Optional[datetime] = None
    event_end_date: Optional[datetime] = None
    
    # JSON fields
    category_ids: Optional[List] = None
    related_news_ids: Optional[List] = None

class NewsArticleResponse(BaseModel):
    uid: UUID  # Database uses uid as primary key
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[str] = None
    published: bool
    is_published: bool
    featured: bool
    allow_comments: bool
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None
    contact_info: Optional[str] = None
    author_name: Optional[str] = None
    category: Optional[str] = None
    
    # Event-related fields
    venue: Optional[str] = None
    location: Optional[str] = None
    registration_link: Optional[str] = None
    ticket_price: Optional[str] = None
    event_start_date: Optional[datetime] = None
    event_end_date: Optional[datetime] = None
    
    # Timestamps
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # JSON fields
    category_ids: Optional[List] = []
    related_news_ids: Optional[List] = []
    
    @field_serializer('uid')
    def serialize_uid(self, value: UUID) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)

class NewsArticleListItem(BaseModel):
    uid: UUID  # Database uses uid as primary key
    title: str
    slug: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[str] = None
    published: bool
    is_published: bool
    featured: bool
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('uid')
    def serialize_uid(self, value: UUID) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)
