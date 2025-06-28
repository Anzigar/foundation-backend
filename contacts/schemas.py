from datetime import datetime
from typing import Optional
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
    id: int
    created_at: datetime
    responded: bool = False
    responded_at: Optional[datetime] = None
    responded_by: Optional[int] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v
        }

class ContactUpdate(BaseModel):
    responded: bool = True
    responded_by: int

# Newsletter schemas
class NewsletterSubscriptionBase(BaseModel):
    email: str
    name: Optional[str] = None
    source: str = "Website"

class NewsletterSubscriptionCreate(NewsletterSubscriptionBase):
    pass

class NewsletterSubscriptionResponse(NewsletterSubscriptionBase):
    id: int
    subscribed_at: datetime
    is_active: bool = True
