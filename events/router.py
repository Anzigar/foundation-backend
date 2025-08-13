from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile, Form
from fastapi.responses import JSONResponse
from uuid import UUID

from events.schemas import (
    EventCreate, 
    EventResponse, 
    EventUpdate, 
    EventRegistrationCreate,
    EventRegistrationResponse
)
from shared.utils import generate_slug
from shared.helpers import fetch_all, fetch_one, execute_query
from shared.storage import storage

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_events(
    cursor: Optional[str] = Query(None, description="Pagination cursor (ID of the last item)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    order: str = Query("desc", description="Sort order (asc or desc)"),
    upcoming: Optional[bool] = Query(None, description="Filter for upcoming events only"),
    featured: Optional[bool] = Query(None, description="Filter by featured status"),
    search: Optional[str] = Query(None, description="Search in title or description")
):
    """
    Get paginated events with cursor-based pagination using raw SQL.
    Implements:
    - Cursor-based pagination
    - Field projection
    """
    # Base query with field projection
    query = """
    SELECT 
        uid, title, slug, excerpt, location, venue_details, start_date,
        image_url, published, featured
    FROM events
    WHERE published = true
    """
    
    params = []
    
    # Apply filters
    if upcoming:
        query += " AND start_date >= %s"
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    if featured is not None:
        query += " AND featured = %s"
        params.append(featured)
    
    if search:
        query += " AND (title ILIKE %s OR description ILIKE %s)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
    
    # Apply cursor pagination
    if cursor:
        if order.lower() == "desc":
            query += " AND uid < %s"
        else:
            query += " AND uid > %s"
        params.append(cursor)
    
    # Order the results
    if order.lower() == "desc":
        query += " ORDER BY uid DESC"
    else:
        query += " ORDER BY uid ASC"
    
    # Get one more item to check if there are more results
    query += f" LIMIT {limit + 1}"
    
    # Execute the query with parameters
    events = await fetch_all(query, tuple(params) if params else None)
    
    # Check if there are more results
    has_more = len(events) > limit
    if has_more:
        events = events[:limit]
    
    # Get the next cursor
    next_cursor = str(events[-1]["uid"]) if has_more and events else None
    
    return {
        "items": events,
        "next_cursor": next_cursor,
        "has_more": has_more
    }

@router.get("/{identifier}", response_model=EventResponse)
async def get_event(identifier: str):
    """Get a single event by UUID or slug using raw SQL."""
    # Try to determine if identifier is a UUID or slug
    try:
        # Try to parse as UUID
        event_uuid = UUID(identifier)
        # Get event by UUID
        query = """
        SELECT * FROM events
        WHERE uid = %s AND published = true
        """
        event = await fetch_one(query, (str(event_uuid),))
    except ValueError:
        # Get event by slug
        query = """
        SELECT * FROM events
        WHERE slug = %s AND published = true
        """
        event = await fetch_one(query, (identifier,))
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Transform the database response to match the schema
    event_dict = dict(event)
    event_dict.update({
        'organizer_id': None,
        'view_count': 0,
        'share_count': 0,
        'comment_count': 0,
        'categories': [],
        'related_events': []
    })
    
    return event_dict

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate):
    """Create a new event using raw SQL with proper transaction handling."""
    from shared.database import async_session
    
    # Generate slug if not provided
    if not event.slug:
        event.slug = generate_slug(event.title)
    
    # Insert the event (let database auto-generate uid)
    query = """
    INSERT INTO events 
    (title, slug, description, excerpt, location, venue_details, start_date, end_date, image_url, published, featured)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING uid
    """
    
    # Convert timezone-aware datetime to timezone-naive for database compatibility
    start_date_naive = event.start_date.replace(tzinfo=None) if event.start_date and event.start_date.tzinfo else event.start_date
    end_date_naive = event.end_date.replace(tzinfo=None) if event.end_date and event.end_date.tzinfo else event.end_date
    
    try:
        async with async_session() as session:
            # Execute INSERT within the session
            result = await fetch_one(
                query, 
                (
                    event.title, 
                    event.slug, 
                    event.description,
                    event.excerpt, 
                    event.location,
                    event.venue_details,
                    start_date_naive,
                    end_date_naive,
                    event.image_url, 
                    event.published, 
                    event.featured
                ),
                db=session
            )
            
            if not result:
                raise HTTPException(status_code=500, detail="Failed to create event")
                
            event_uid = result["uid"]
            
            # Get the newly created event within the same session
            new_event = await fetch_one("SELECT * FROM events WHERE uid = %s", (str(event_uid),), db=session)
            
            if not new_event:
                raise HTTPException(status_code=500, detail="Failed to retrieve created event")
            
            # Commit the transaction
            await session.commit()
            
            # Transform the database response to match the schema
            event_dict = dict(new_event)
            event_dict.update({
                'organizer_id': None,
                'view_count': 0,
                'share_count': 0,
                'comment_count': 0,
                'categories': [],
                'related_events': []
            })
            
            return event_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.put("/{event_uid}", response_model=EventResponse)
async def update_event(event_uid: UUID, event_update: EventUpdate):
    """Update an existing event using raw SQL."""
    # First check if the event exists
    existing = await fetch_one("SELECT slug FROM events WHERE uid = %s", (str(event_uid),))
    
    if not existing:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Build the update query dynamically based on provided fields
    update_fields = []
    params = []
    
    if event_update.title is not None:
        update_fields.append("title = %s")
        params.append(event_update.title)
        # Also update slug if title is provided
        slug = generate_slug(event_update.title)
        update_fields.append("slug = %s")
        params.append(slug)
    
    if event_update.description is not None:
        update_fields.append("description = %s")
        params.append(event_update.description)
    
    if event_update.location is not None:
        update_fields.append("location = %s")
        params.append(event_update.location)
    
    if event_update.venue_details is not None:
        update_fields.append("venue_details = %s")
        params.append(event_update.venue_details)
    
    if event_update.image_url is not None:
        update_fields.append("image_url = %s")
        params.append(event_update.image_url)
    
    if event_update.published is not None:
        update_fields.append("published = %s")
        params.append(event_update.published)
    
    if event_update.featured is not None:
        update_fields.append("featured = %s")
        params.append(event_update.featured)
    
    # Update the event if there are fields to update
    if update_fields:
        update_query = f"""
        UPDATE events 
        SET {', '.join(update_fields)}
        WHERE uid = %s
        """
        
        params.append(str(event_uid))
        await execute_query(update_query, tuple(params))
    
    # Get the updated event by UID
    updated_event = await fetch_one("SELECT * FROM events WHERE uid = %s", (str(event_uid),))
    
    # Transform the database response to match the schema
    event_dict = dict(updated_event)
    event_dict.update({
        'organizer_id': None,
        'view_count': 0,
        'share_count': 0,
        'comment_count': 0,
        'categories': [],
        'related_events': []
    })
    
    return event_dict

@router.delete("/{event_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_uid: UUID):
    """Delete an event using raw SQL."""
    # Get the slug before deletion to clear cache
    event = await fetch_one(
        "SELECT slug FROM events WHERE uid = %s", 
        (str(event_uid),)
    )
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Delete the event (registrations will be deleted via ON DELETE CASCADE)
    await execute_query("DELETE FROM events WHERE uid = %s", (str(event_uid),))
    
    return JSONResponse(content={}, status_code=status.HTTP_204_NO_CONTENT)

# Event registration routes
@router.post("/{event_uid}/register", response_model=EventRegistrationResponse)
async def register_for_event(event_uid: UUID, registration: EventRegistrationCreate):
    """Register for an event."""
    # Check if event exists and is published
    event = await fetch_one(
        "SELECT uid FROM events WHERE uid = %s AND published = true", 
        (str(event_uid),)
    )
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or not published")
    
    # Create registration
    query = """
    INSERT INTO event_registrations (event_uid, name, email, phone)
    VALUES (%s, %s, %s, %s)
    """
    
    await execute_query(
        query,(str(event_uid), registration.name, registration.email, registration.phone)
    )
    
    registration_uid = await fetch_one("SELECT LAST_INSERT_ID() as uid")
    
    # Get the registration details
    new_registration = await fetch_one(
        "SELECT * FROM event_registrations WHERE uid = %s", 
        (registration_uid["uid"],)
    )
    
    return new_registration

@router.get("/{event_uid}/registrations", response_model=List[EventRegistrationResponse])
async def get_event_registrations(event_uid: UUID):
    """Get all registrations for an event."""
    # Check if event exists
    event = await fetch_one("SELECT uid FROM events WHERE uid = %s", (str(event_uid),))
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get registrations
    registrations = await fetch_all(
        "SELECT * FROM event_registrations WHERE event_uid = %s ORDER BY created_at DESC", 
        (str(event_uid),)
    )
    
    return registrations

# Image upload endpoint
@router.post("/{event_uid}/upload-image")
async def upload_event_image(
    event_uid: UUID,
    image: UploadFile = File(..., description="Event image file")
):
    """Upload an image for an event to S3."""
    # Check if event exists
    event = await fetch_one("SELECT uid FROM events WHERE uid = %s", (str(event_uid),))
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only JPEG, PNG, GIF, and WebP images are allowed."
        )
    
    # Upload image to S3 with encoded path
    success, message, encoded_image_path = await storage.upload_file(
        file=image,
        folder=f"events/{event_uid}",
        custom_filename=None,  # Let it generate a secure filename
        encode_path=True  # Return encoded path for security
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {message}")
    
    # Update event with the encoded image path (stored as image_url in database)
    await execute_query(
        "UPDATE events SET image_url = %s WHERE uid = %s", 
        (encoded_image_path, str(event_uid))
    )
    
    return {
        "success": True,
        "message": "Image uploaded successfully",
        "encoded_path": encoded_image_path,
        "actual_url": storage.get_actual_url(encoded_image_path)
    }

@router.delete("/{event_uid}/image")
async def delete_event_image(event_uid: UUID):
    """Delete an event's image from S3 and database."""
    # Get current image URL
    event = await fetch_one(
        "SELECT image_url FROM events WHERE uid = %s", 
        (str(event_uid),)
    )
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if not event["image_url"]:
        raise HTTPException(status_code=404, detail="Event has no image to delete")
    
    # Delete from S3 (handles both encoded paths and full URLs)
    success, message = storage.delete_file(event["image_url"])
    
    if success:
        # Remove image URL from database
        await execute_query(
            "UPDATE events SET image_url = NULL WHERE uid = %s", 
            (str(event_uid),)
        )
        
        return {"success": True, "message": "Image deleted successfully"}
    else:
        # Still remove from database even if S3 deletion failed
        await execute_query(
            "UPDATE events SET image_url = NULL WHERE uid = %s", 
            (str(event_uid),)
        )
        
        return {
            "success": False, 
            "message": f"Warning: S3 deletion failed ({message}), but image URL removed from database"
        }

@router.get("/{event_uid}/image-url")
async def get_event_image_url(event_uid: UUID):
    """Get the actual S3 image URL from the encoded path stored in database."""
    # Get event with image URL/encoded path
    event = await fetch_one(
        "SELECT image_url FROM events WHERE uid = %s", 
        (str(event_uid),)
    )
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if not event["image_url"]:
        raise HTTPException(status_code=404, detail="Event has no image")
    
    # Get the actual URL (decodes if it's encoded)
    actual_url = storage.get_actual_url(event["image_url"])
    
    return {
        "encoded_path": event["image_url"],
        "actual_url": actual_url
    }
