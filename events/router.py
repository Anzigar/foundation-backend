from datetime import datetime
from typing import List, Optional, Dict, Any
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
        id, title, slug, excerpt, location, event_date,
        image_url, author_name, is_published, featured
    FROM events
    WHERE is_published = true
    """
    
    params = []
    
    # Apply filters
    if upcoming:
        query += " AND event_date >= %s"
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    if featured is not None:
        query += " AND featured = %s"
        params.append(featured)
    
    if search:
        query += " AND (title ILIKE %s OR content ILIKE %s)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
    
    # Apply cursor pagination
    if cursor:
        if order.lower() == "desc":
            query += " AND id < %s"
        else:
            query += " AND id > %s"
        params.append(cursor)
    
    # Order the results
    if order.lower() == "desc":
        query += " ORDER BY id DESC"
    else:
        query += " ORDER BY id ASC"
    
    # Get one more item to check if there are more results
    query += f" LIMIT {limit + 1}"
    
    # Execute the query with parameters
    events = await fetch_all(query, tuple(params) if params else None)
    
    # Check if there are more results
    has_more = len(events) > limit
    if has_more:
        events = events[:limit]
    
    # Get the next cursor
    next_cursor = str(events[-1]["id"]) if has_more and events else None
    
    return {
        "items": events,
        "next_cursor": next_cursor,
        "has_more": has_more
    }

@router.get("/id/{event_id}", response_model=EventResponse)
async def get_event_by_id(event_id: int):
    """Get a single event by ID using raw SQL."""
    query = """
    SELECT * FROM events
    WHERE id = %s AND is_published = true
    """
    
    event = await fetch_one(query, (event_id,))
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event

@router.get("/{slug}", response_model=EventResponse)
async def get_event(slug: str):
    """Get a single event by slug using raw SQL."""
    query = """
    SELECT * FROM events
    WHERE slug = %s AND is_published = true
    """
    
    event = await fetch_one(query, (slug,))
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(event: EventCreate):
    """Create a new event using raw SQL."""
    # Generate slug if not provided
    if not event.slug:
        event.slug = generate_slug(event.title)
    
    # Insert the event
    query = """
    INSERT INTO events 
    (title, slug, content, excerpt, location, event_date, image_url, author_name, is_published, featured)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    # Convert timezone-aware datetime to timezone-naive for database compatibility
    event_date_naive = event.event_date.replace(tzinfo=None) if event.event_date and event.event_date.tzinfo else event.event_date
    
    await execute_query(
        query, 
        (
            event.title, 
            event.slug, 
            event.content,
            event.excerpt, 
            event.location, 
            event_date_naive,
            event.image_url, 
            event.author_name,
            event.is_published, 
            event.featured
        )
    )
    
    # Get the newly created event
    return await get_event(event.slug)

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(event_id: int, event_update: EventUpdate):
    """Update an existing event using raw SQL."""
    # First check if the event exists
    existing = await fetch_one("SELECT slug FROM events WHERE id = %s", (event_id,))
    
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
        update_fields.append("content = %s")
        params.append(event_update.description)
    
    if event_update.location is not None:
        update_fields.append("location = %s")
        params.append(event_update.location)
    
    if event_update.image_url is not None:
        update_fields.append("image_url = %s")
        params.append(event_update.image_url)
    
    if event_update.published is not None:
        update_fields.append("is_published = %s")
        params.append(event_update.published)
    
    if event_update.featured is not None:
        update_fields.append("featured = %s")
        params.append(event_update.featured)
    
    # Update the event if there are fields to update
    if update_fields:
        update_query = f"""
        UPDATE events 
        SET {', '.join(update_fields)}
        WHERE id = %s
        """
        
        params.append(event_id)
        await execute_query(update_query, tuple(params))
    
    # Get the updated event
    return await get_event(existing["slug"])

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int):
    """Delete an event using raw SQL."""
    # Get the slug before deletion to clear cache
    event = await fetch_one(
        "SELECT slug FROM events WHERE id = %s", 
        (event_id,)
    )
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Delete the event (registrations will be deleted via ON DELETE CASCADE)
    await execute_query("DELETE FROM events WHERE id = %s", (event_id,))
    
    return JSONResponse(content={}, status_code=status.HTTP_204_NO_CONTENT)

# Event registration routes
@router.post("/{event_id}/register", response_model=EventRegistrationResponse)
async def register_for_event(event_id: int, registration: EventRegistrationCreate):
    """Register for an event."""
    # Check if event exists and is published
    event = await fetch_one(
        "SELECT id FROM events WHERE id = %s AND is_published = true", 
        (event_id,)
    )
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or not published")
    
    # Create registration
    query = """
    INSERT INTO event_registrations (event_id, name, email, phone)
    VALUES (%s, %s, %s, %s)
    """
    
    await execute_query(
        query,(event_id, registration.name, registration.email, registration.phone)
    )
    
    registration_id = await fetch_one("SELECT LAST_INSERT_ID() as id")
    
    # Get the registration details
    new_registration = await fetch_one(
        "SELECT * FROM event_registrations WHERE id = %s", 
        (registration_id["id"],)
    )
    
    return new_registration

@router.get("/{event_id}/registrations", response_model=List[EventRegistrationResponse])
async def get_event_registrations(event_id: int):
    """Get all registrations for an event."""
    # Check if event exists
    event = await fetch_one("SELECT id FROM events WHERE id = %s", (event_id,))
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get registrations
    registrations = await fetch_all(
        "SELECT * FROM event_registrations WHERE event_id = %s ORDER BY created_at DESC", 
        (event_id,)
    )
    
    return registrations
