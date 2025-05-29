from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class ContactBase(BaseModel):
    name: str
    email: str
    phoneNumber: Optional[str] = None  # Added phone number field
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
        # Allow conversion from strings for datetime fields
        json_encoders = {
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v
        }

class ContactUpdate(BaseModel):
    responded: bool = True
    responded_by: int
