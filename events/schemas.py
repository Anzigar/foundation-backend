from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, HttpUrl

class EventCategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

class EventCategoryCreate(EventCategoryBase):
    pass

class EventCategoryResponse(EventCategoryBase):
    id: int

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
    allow_comments: bool = True
    seo_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None

class EventCreate(EventBase):
    slug: Optional[str] = None  # Will be generated if not provided
    category_ids: List[int] = []
    related_event_ids: Optional[List[int]] = None

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
    category_ids: Optional[List[int]] = None
    related_event_ids: Optional[List[int]] = None

class EventResponse(EventBase):
    id: int
    slug: str
    organizer_id: Optional[int] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    view_count: int = 0
    share_count: int = 0
    comment_count: int = 0
    categories: List[EventCategoryResponse] = []
    related_events: Optional[List[Dict[str, Any]]] = None

class EventListItem(BaseModel):
    id: int
    title: str
    slug: str
    location: Optional[str]
    start_date: datetime
    end_date: Optional[datetime]
    image_url: Optional[str]
    organizer_id: Optional[int] = None
    published: bool
    featured: bool

class EventRegistrationCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None

class EventRegistrationResponse(EventRegistrationCreate):
    id: int
    event_id: int
    created_at: datetime

class EventCommentBase(BaseModel):
    author_name: str
    author_email: EmailStr
    content: str
    parent_id: Optional[int] = None

class EventCommentCreate(EventCommentBase):
    pass

class EventCommentResponse(EventCommentBase):
    id: int
    event_id: int
    is_approved: bool
    created_at: datetime
    replies: Optional[List["EventCommentResponse"]] = []
