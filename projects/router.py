from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status, File, UploadFile, Form
from fastapi.responses import JSONResponse

from projects.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectImageUpdate,
    ProjectImageResponse
)
from shared.utils import generate_slug
from shared.database import get_db
from shared.storage import storage
from shared.helpers import fetch_all, fetch_one, execute_query

router = APIRouter()

# Constants
PROJECT_NOT_FOUND = "Project not found"
IMAGE_NOT_FOUND = "Image not found"

@router.get("/", response_model=Dict[str, Any])
async def get_projects(
    cursor: Optional[str] = Query(None, description="Pagination cursor (ID of the last item)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    order: str = Query("desc", description="Sort order (asc or desc)"),
    featured: Optional[bool] = Query(None, description="Filter by featured status"),
    search: Optional[str] = Query(None, description="Search in title or description")
):
    """Get paginated projects with cursor-based pagination."""
    # Base query - updated to match actual database structure
    query = """
    SELECT 
        uid, title, slug, description, excerpt, content, status, 
        published, featured, created_at, updated_at,
        image_url, category_ids
    FROM projects
    WHERE published = true
    """
    
    params = []
    
    # Apply filters
    if featured is not None:
        query += " AND featured = %s"
        params.append(featured)
    
    if search:
        query += " AND (title LIKE %s OR description LIKE %s)"
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
    projects = await fetch_all(query, tuple(params) if params else None)
    
    # Format projects
    formatted_projects = []
    
    for item in projects:
        project = {
            "id": item["uid"],
            "title": item["title"],
            "slug": item["slug"],
            "description": item["description"],
            "excerpt": item["excerpt"],
            "content": item["content"],
            "status": item["status"],
            "published": bool(item["published"]),
            "featured": bool(item["featured"]),
            "image_url": item["image_url"],
            "category_ids": item["category_ids"],
            "created_at": item["created_at"],
            "updated_at": item["updated_at"]
        }
        formatted_projects.append(project)
    
    # Check if there are more results
    has_more = len(formatted_projects) > limit
    if has_more:
        formatted_projects = formatted_projects[:limit]
    
    # Get the next cursor
    next_cursor = str(formatted_projects[-1]["id"]) if has_more and formatted_projects else None
    
    return {
        "items": formatted_projects,
        "next_cursor": next_cursor,
        "has_more": has_more
    }

@router.get("/{identifier}", response_model=ProjectResponse)
async def get_project(identifier: str):
    """Get a single project by slug or ID."""
    # Try to determine if identifier is a UUID or slug
    try:
        # Try to parse as UUID
        project_uuid = UUID(identifier)
        # Get project by UUID
        project_query = "SELECT * FROM projects WHERE uid = %s AND published = true"
        project = await fetch_one(project_query, (project_uuid,))
    except ValueError:
        # Get project by slug
        project_query = "SELECT * FROM projects WHERE slug = %s AND published = true"
        project = await fetch_one(project_query, (identifier,))
    
    if not project:
        raise HTTPException(status_code=404, detail=PROJECT_NOT_FOUND)
    
    # Convert project to dict and return (no images in this schema)
    project_dict = dict(project)
    project_dict["id"] = project_dict["uid"]  # Map uid to id for response
    project_dict["images"] = []  # Empty images list for compatibility
    
    return project_dict

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate):
    """Create a new project."""
    # Generate slug if not provided
    if not project.slug:
        project.slug = generate_slug(project.title)
    
    # Check for slug uniqueness
    existing = await fetch_one("SELECT uid FROM projects WHERE slug = %s", (project.slug,))
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Project with slug '{project.slug}' already exists"
        )
    
    # Insert the project
    query = """
    INSERT INTO projects (
        uid, title, slug, description, excerpt, content, status, published, featured,
        image_url, category_ids
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    # Convert technologies to JSON string
    import json
    import uuid
    project_uid = uuid.uuid4()
    
    await execute_query(
        query, 
        (
            project_uid,
            project.title, 
            project.slug, 
            project.description,
            project.excerpt or project.description[:500] if project.description else None,  # excerpt
            project.content or project.description,  # content
            project.status,  # status from schema
            project.published,  # published from schema
            project.featured,
            project.image_url,  # image_url from schema
            "[]"  # empty category_ids
        )
    )
    
    # Get the created project
    result = await fetch_one("SELECT * FROM projects WHERE slug = %s", (project.slug,))
    
    # Return the newly created project
    return await get_project(str(result["uid"]))

@router.put("/{project_uid}", response_model=ProjectResponse)
async def update_project(project_uid: str, project_update: ProjectUpdate):
    """Update an existing project."""
    # Check if project exists
    existing = await fetch_one("SELECT slug FROM projects WHERE uid = %s", (project_uid,))
    
    if not existing:
        raise HTTPException(status_code=404, detail=PROJECT_NOT_FOUND)
    
    # Build the update query dynamically based on provided fields
    update_fields = []
    params = []
    
    if project_update.title is not None:
        update_fields.append("title = %s")
        params.append(project_update.title)
        # Also update slug if title is provided
        new_slug = generate_slug(project_update.title)
        update_fields.append("slug = %s")
        params.append(new_slug)
    
    if project_update.description is not None:
        update_fields.append("description = %s")
        params.append(project_update.description)
    
    if project_update.featured is not None:
        update_fields.append("featured = %s")
        params.append(project_update.featured)
    
    if project_update.published is not None:
        update_fields.append("published = %s")
        params.append(project_update.published)
    
    # Update timestamp
    update_fields.append("updated_at = %s")
    params.append(datetime.now())
    
    # Update the project if there are fields to update
    if update_fields:
        update_query = f"""
        UPDATE projects 
        SET {', '.join(update_fields)}
        WHERE uid = %s
        """
        
        params.append(project_uid)
        await execute_query(update_query, tuple(params))
    
    # Get the updated project
    updated_project = await fetch_one("SELECT uid FROM projects WHERE uid = %s", (project_uid,))
    return await get_project(str(updated_project["uid"]))

@router.delete("/{project_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_uid: UUID):
    """Delete a project."""
    # Check if project exists
    existing = await fetch_one("SELECT uid FROM projects WHERE uid = %s", (project_uid,))
    
    if not existing:
        raise HTTPException(status_code=404, detail=PROJECT_NOT_FOUND)
    
    # Delete the project (images will be deleted via CASCADE)
    await execute_query("DELETE FROM projects WHERE uid = %s", (project_uid,))
    
    return JSONResponse(content={}, status_code=status.HTTP_204_NO_CONTENT)

# Image upload endpoint
@router.post("/{project_uid}/upload-image")
async def upload_project_image(
    project_uid: UUID,
    image: UploadFile = File(..., description="Project image file")
):
    """Upload an image for a project to S3."""
    # Check if project exists
    project = await fetch_one("SELECT uid FROM projects WHERE uid = %s", (str(project_uid),))
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
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
        folder=f"projects/{project_uid}",
        custom_filename=None,  # Let it generate a secure filename
        encode_path=True  # Return encoded path for security
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {message}")
    
    # Update project with the encoded image path
    await execute_query(
        "UPDATE projects SET image_url = %s WHERE uid = %s", 
        (encoded_image_path, str(project_uid))
    )
    
    return {
        "success": True,
        "message": "Image uploaded successfully",
        "encoded_path": encoded_image_path,
        "actual_url": storage.get_actual_url(encoded_image_path)
    }

@router.delete("/{project_uid}/image")
async def delete_project_image(project_uid: UUID):
    """Delete a project's image from S3 and database."""
    # Get current image URL/encoded path
    project = await fetch_one(
        "SELECT image_url FROM projects WHERE uid = %s", 
        (str(project_uid),)
    )
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project["image_url"]:
        raise HTTPException(status_code=404, detail="Project has no image to delete")
    
    # Delete from S3 (handles both encoded paths and full URLs)
    success, message = storage.delete_file(project["image_url"])
    
    if success:
        # Remove image URL from database
        await execute_query(
            "UPDATE projects SET image_url = NULL WHERE uid = %s", 
            (str(project_uid),)
        )
        
        return {"success": True, "message": "Image deleted successfully"}
    else:
        # Still remove from database even if S3 deletion failed
        await execute_query(
            "UPDATE projects SET image_url = NULL WHERE uid = %s", 
            (str(project_uid),)
        )
        
        return {
            "success": False, 
            "message": f"Warning: S3 deletion failed ({message}), but image URL removed from database"
        }

@router.get("/{project_uid}/image-url")
async def get_project_image_url(project_uid: UUID):
    """Get the actual S3 image URL from the encoded path stored in database."""
    # Get project with image URL/encoded path
    project = await fetch_one(
        "SELECT image_url FROM projects WHERE uid = %s", 
        (str(project_uid),)
    )
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project["image_url"]:
        raise HTTPException(status_code=404, detail="Project has no image")
    
    # Get the actual URL (decodes if it's encoded)
    actual_url = storage.get_actual_url(project["image_url"])
    
    return {
        "encoded_path": project["image_url"],
        "actual_url": actual_url
    }
