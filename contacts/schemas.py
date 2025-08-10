from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

class ContactBase(BaseModel):
    full_name: str
    email: str
    phone_number: Optional[str] = None
    subject: str
    message: str

class ContactCreate(ContactBase):
    pass

class ContactResponse(ContactBase):
    id: UUID
    created_at: Optional[datetime] = None
    responded: Optional[bool] = False
    responded_at: Optional[datetime] = None
    responded_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v
        }

class ContactUpdate(BaseModel):
    responded: bool = True
    responded_by: UUID

# Newsletter schemas
class NewsletterSubscriptionBase(BaseModel):
    email: str
    name: Optional[str] = None
    source: str = "Website"

class NewsletterSubscriptionCreate(NewsletterSubscriptionBase):
    pass

class NewsletterSubscriptionResponse(NewsletterSubscriptionBase):
    id: UUID
    subscribed_at: datetime
    is_active: bool = True
