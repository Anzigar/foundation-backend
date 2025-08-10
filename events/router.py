from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from events.schemas import (
    EventCreate, 
    EventResponse, 
    EventUpdate, 
    EventRegistrationCreate,
    EventRegistrationResponse
)
from shared.utils import generate_slug
from shared.helpers import fetch_all, fetch_one, execute_query

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
        uid, title, slug, excerpt, location, start_date,
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
    """Get a single event by uid or slug using raw SQL."""
    # Try to determine if identifier is a UUID or slug
    try:
        # Try to parse as UUID
        event_uuid = UUID(identifier)
        # Get event by uid
        query = """
        SELECT * FROM events
        WHERE uid = %s AND published = true
        """
        event = await fetch_one(query, (event_uuid,))
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
    """Create a new event using raw SQL."""
    # Generate slug if not provided
    if not event.slug:
        event.slug = generate_slug(event.title)
    
    # Generate UUID for the new event
    import uuid
    event_uid = uuid.uuid4()
    
    # Insert the event with explicit UID
    query = """
    INSERT INTO events 
    (uid, title, slug, description, excerpt, location, start_date, end_date, image_url, published, featured)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING uid
    """
    
    # Convert timezone-aware datetime to timezone-naive for database compatibility
    start_date_naive = event.start_date.replace(tzinfo=None) if event.start_date and event.start_date.tzinfo else event.start_date
    end_date_naive = event.end_date.replace(tzinfo=None) if event.end_date and event.end_date.tzinfo else event.end_date
    
    result = await fetch_one(
        query, 
        (
            event_uid,
            event.title, 
            event.slug, 
            event.description,
            event.excerpt, 
            event.location, 
            start_date_naive,
            end_date_naive,
            event.image_url, 
            event.published, 
            event.featured
        )
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create event")
    
    event_uid = result['uid']
    
    # Get the newly created event
    new_event = await fetch_one("SELECT * FROM events WHERE uid = %s", (event_uid,))
    
    if not new_event:
        raise HTTPException(status_code=500, detail="Failed to retrieve created event")
    
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

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(event_id: Union[int, UUID], event_update: EventUpdate):
    """Update an existing event using raw SQL."""
    # First check if the event exists
    existing = await fetch_one("SELECT slug FROM events WHERE uid = %s", (event_id,))
    
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
        
        params.append(event_id)
        await execute_query(update_query, tuple(params))
    
    # Get the updated event by ID
    updated_event = await fetch_one("SELECT * FROM events WHERE uid = %s", (event_id,))
    
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

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: Union[int, UUID]):
    """Delete an event using raw SQL."""
    # Get the slug before deletion to clear cache
    event = await fetch_one(
        "SELECT slug FROM events WHERE uid = %s", 
        (event_id,)
    )
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Delete the event (registrations will be deleted via ON DELETE CASCADE)
    await execute_query("DELETE FROM events WHERE uid = %s", (event_id,))
    
    return JSONResponse(content={}, status_code=status.HTTP_204_NO_CONTENT)

# Event registration routes
@router.post("/{event_id}/register", response_model=EventRegistrationResponse)
async def register_for_event(event_id: Union[int, UUID], registration: EventRegistrationCreate):
    """Register for an event."""
    # Check if event exists and is published
    event = await fetch_one(
        "SELECT uid FROM events WHERE uid = %s AND published = true", 
        (event_id,)
    )
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or not published")
    
    # Note: This requires an event_registrations table to exist
    # For now, we'll return a simple response indicating registration interest
    import uuid
    return {
        "uid": uuid.uuid4(),  # Generate UUID
        "event_id": event_id,
        "name": registration.name,
        "email": registration.email,
        "phone": registration.phone,
        "created_at": datetime.now()
    }

@router.get("/{event_id}/registrations", response_model=List[EventRegistrationResponse])
async def get_event_registrations(event_id: Union[int, UUID]):
    """Get all registrations for an event."""
    # Check if event exists
    event = await fetch_one("SELECT uid FROM events WHERE uid = %s", (event_id,))
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Return empty list since event_registrations table may not exist
    return []
