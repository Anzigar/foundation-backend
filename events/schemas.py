from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, HttpUrl, field_serializer

class EventCategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

class EventCategoryCreate(EventCategoryBase):
    pass

class EventCategoryResponse(EventCategoryBase):
    id: UUID  # Keep as UUID in schema
    
    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)

class EventBase(BaseModel):
    title: str
    description: str
    excerpt: Optional[str] = None
    location: Optional[str] = None
    venue_details: Optional[str] = None
    map_embed_url: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    image_url: Optional[str] = None
    ticket_price: Optional[str] = None
    registration_link: Optional[str] = None
    rsvp_enabled: bool = False
    contact_info: Optional[str] = None
    tags: Optional[str] = None
    published: bool = False
    featured: bool = False
    allow_comments: Optional[bool] = True  # Allow None values with default
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None

class EventCreate(EventBase):
    slug: Optional[str] = None  # Will be generated if not provided
    category_ids: List[str] = []  # Accept category IDs as strings for flexibility
    related_event_ids: Optional[List[str]] = None

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    excerpt: Optional[str] = None
    location: Optional[str] = None
    venue_details: Optional[str] = None
    map_embed_url: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    image_url: Optional[str] = None
    ticket_price: Optional[str] = None
    registration_link: Optional[str] = None
    rsvp_enabled: Optional[bool] = None
    contact_info: Optional[str] = None
    tags: Optional[str] = None
    published: Optional[bool] = None
    featured: Optional[bool] = None
    allow_comments: Optional[bool] = None
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None
    category_ids: Optional[List[str]] = None  # Accept category IDs as strings for flexibility
    related_event_ids: Optional[List[str]] = None

class EventResponse(EventBase):
    id: UUID  # Keep as UUID in schema
    slug: str
    organizer_id: Optional[UUID] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    view_count: int = 0
    share_count: int = 0
    comment_count: int = 0
    categories: List[EventCategoryResponse] = []
    related_events: Optional[List[Dict[str, Any]]] = None
    
    @field_serializer('id', 'organizer_id')
    def serialize_uuid(self, value: Optional[UUID]) -> Optional[str]:
        """Convert UUID to string for JSON serialization"""
        return str(value) if value else None
    
    class Config:
        from_attributes = True
        extra = "ignore"

class EventListItem(BaseModel):
    id: UUID  # Keep as UUID in schema
    title: str
    slug: str
    location: Optional[str]
    start_date: datetime
    end_date: Optional[datetime]
    image_url: Optional[str]
    organizer_id: Optional[UUID] = None
    published: bool
    featured: bool
    
    @field_serializer('id', 'organizer_id')
    def serialize_uuid(self, value: Optional[UUID]) -> Optional[str]:
        """Convert UUID to string for JSON serialization"""
        return str(value) if value else None

class EventRegistrationCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None

class EventRegistrationResponse(EventRegistrationCreate):
    id: UUID
    event_id: UUID
    created_at: datetime

class EventCommentBase(BaseModel):
    author_name: str
    author_email: EmailStr
    content: str
    parent_id: Optional[UUID] = None

class EventCommentCreate(EventCommentBase):
    pass

class EventCommentResponse(EventCommentBase):
    id: UUID
    event_id: UUID
    is_approved: bool
    created_at: datetime
    replies: Optional[List["EventCommentResponse"]] = []
