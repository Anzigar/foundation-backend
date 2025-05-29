from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile, Form
from fastapi.responses import JSONResponse

from projects.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListItem,
    ProjectImageCreate,
    ProjectImageUpdate,
    ProjectImageResponse
)
from shared.utils import generate_slug
from api.uploads import upload_image

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_projects(
    cursor: Optional[str] = Query(None, description="Pagination cursor (ID of the last item)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    order: str = Query("desc", description="Sort order (asc or desc)"),
    featured: Optional[bool] = Query(None, description="Filter by featured status"),
    search: Optional[str] = Query(None, description="Search in title or description")
):
    """
    Get paginated projects with cursor-based pagination.
    """
    # Base query
    query = """
    SELECT 
        p.id, p.title, p.slug, p.description, p.timeline, 
        p.featured, p.created_at,
        i.id as image_id, i.title as image_title, 
        i.description as image_description, i.image_url
    FROM projects p
    LEFT JOIN project_images i ON p.id = i.project_id AND i.primary = true
    WHERE p.published = true
    """
    
    params = []
    
    # Apply filters
    if featured is not None:
        query += " AND p.featured = %s"
        params.append(featured)
    
    if search:
        query += " AND (p.title ILIKE %s OR p.description ILIKE %s)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
    
    # Apply cursor pagination
    if cursor:
        if order.lower() == "desc":
            query += " AND p.id < %s"
        else:
            query += " AND p.id > %s"
        params.append(cursor)
    
    # Order the results
    if order.lower() == "desc":
        query += " ORDER BY p.id DESC"
    else:
        query += " ORDER BY p.id ASC"
    
    # Get one more item to check if there are more results
    query += f" LIMIT {limit + 1}"
    
    # Execute the query with parameters
    projects = await fetch_all(query, tuple(params) if params else None)
    
    # Format projects with primary image
    formatted_projects = []
    seen_projects = set()
    
    for item in projects:
        if item["id"] not in seen_projects:
            project = {
                "id": item["id"],
                "title": item["title"],
                "slug": item["slug"],
                "description": item["description"],
                "timeline": item["timeline"],
                "featured": item["featured"],
                "created_at": item["created_at"],
                "primary_image": None
            }
            
            # Add primary image if it exists
            if item["image_id"]:
                project["primary_image"] = {
                    "id": item["image_id"],
                    "title": item["image_title"],
                    "description": item["image_description"],
                    "image_url": item["image_url"],
                    "project_id": item["id"],
                    "primary": True,
                    "order": 0,
                    "created_at": item["created_at"]  # Use project creation date as fallback
                }
            
            formatted_projects.append(project)
            seen_projects.add(item["id"])
    
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

@router.get("/{slug}", response_model=ProjectResponse)
async def get_project(slug: str):
    """Get a single project by slug."""
    # Get project
    project_query = """
    SELECT * FROM projects WHERE slug = %s AND published = true
    """
    
    project = await fetch_one(project_query, (slug,))
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get project images
    images_query = """
    SELECT * FROM project_images 
    WHERE project_id = %s
    ORDER BY "order" ASC, created_at ASC
    """
    
    images = await fetch_all(images_query, (project["id"],))
    
    # Combine project and images
    project["images"] = images or []
    
    # Parse links JSON
    if project["links"] and isinstance(project["links"], str):
        import json
        try:
            project["links"] = json.loads(project["links"])
        except:
            project["links"] = {}
    
    return project

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate):
    """Create a new project."""
    # Generate slug if not provided
    if not project.slug:
        project.slug = generate_slug(project.title)
    
    # Check for slug uniqueness
    existing = await fetch_one("SELECT id FROM projects WHERE slug = %s", (project.slug,))
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Project with slug '{project.slug}' already exists"
        )
    
    # Insert the project
    query = """
    INSERT INTO projects (
        title, slug, description, timeline, links, 
        published, featured
    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING id
    """
    
    # Convert links to JSON string for PostgreSQL
    import json
    links_json = json.dumps(project.links) if project.links else "{}"
    
    result = await fetch_one(
        query, 
        (
            project.title, 
            project.slug, 
            project.description, 
            project.timeline, 
            links_json,
            project.published, 
            project.featured
        )
    )
    
    project_id = result["id"]
    
    # Add images if provided
    if project.images:
        for i, image in enumerate(project.images):
            image_query = """
            INSERT INTO project_images (
                project_id, title, description, image_url, 
                primary, "order"
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            # First image is primary by default if none specified
            is_primary = image.primary or (i == 0 and not any(img.primary for img in project.images))
            
            await execute_query(
                image_query,
                (
                    project_id,
                    image.title,
                    image.description,
                    image.image_url,
                    is_primary,
                    image.order or i
                )
            )
    
    # Return the newly created project
    return await get_project(project.slug)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, project_update: ProjectUpdate):
    """Update an existing project."""
    # Check if project exists
    existing = await fetch_one("SELECT slug FROM projects WHERE id = %s", (project_id,))
    
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
    
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
    
    if project_update.timeline is not None:
        update_fields.append("timeline = %s")
        params.append(project_update.timeline)
    
    if project_update.links is not None:
        import json
        update_fields.append("links = %s")
        params.append(json.dumps(project_update.links))
    
    if project_update.published is not None:
        update_fields.append("published = %s")
        params.append(project_update.published)
    
    if project_update.featured is not None:
        update_fields.append("featured = %s")
        params.append(project_update.featured)
    
    # Update timestamp
    update_fields.append("updated_at = %s")
    params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Update the project if there are fields to update
    if update_fields:
        update_query = f"""
        UPDATE projects 
        SET {', '.join(update_fields)}
        WHERE id = %s
        RETURNING slug
        """
        
        params.append(project_id)
        result = await fetch_one(update_query, tuple(params))
        
        # Get updated slug (in case it changed)
        slug = result["slug"] if result and "slug" in result else existing["slug"]
    else:
        slug = existing["slug"]
    
    # Get the updated project
    return await get_project(slug)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int):
    """Delete a project."""
    # Check if project exists
    existing = await fetch_one("SELECT id FROM projects WHERE id = %s", (project_id,))
    
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete the project (images will be deleted via CASCADE)
    await execute_query("DELETE FROM projects WHERE id = %s", (project_id,))
    
    return JSONResponse(content={}, status_code=status.HTTP_204_NO_CONTENT)

# Project Image Endpoints
@router.post("/{project_id}/images", response_model=ProjectImageResponse, status_code=status.HTTP_201_CREATED)
async def add_project_image(
    project_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    primary: bool = Form(False),
    order: int = Form(0),
    image: UploadFile = File(...),
):
    """Add an image to a project."""
    # Check if project exists
    project = await fetch_one("SELECT id FROM projects WHERE id = %s", (project_id,))
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Upload the image
    success, message, image_url = await upload_image(
        file=image,
        folder=f"project-images/{project_id}",
        filename=None  # Generate a unique filename
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {message}")
    
    # If this is primary, update other images to not be primary
    if primary:
        await execute_query(
            "UPDATE project_images SET primary = false WHERE project_id = %s",
            (project_id,)
        )
    
    # Add the image to the project
    query = """
    INSERT INTO project_images (
        project_id, title, description, image_url, primary, "order"
    ) VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id, created_at
    """
    
    result = await fetch_one(
        query,
        (project_id, title, description, image_url, primary, order)
    )
    
    # Return the newly created image
    return {
        "id": result["id"],
        "project_id": project_id,
        "title": title,
        "description": description,
        "image_url": image_url,
        "primary": primary,
        "order": order,
        "created_at": result["created_at"]
    }

@router.put("/images/{image_id}", response_model=ProjectImageResponse)
async def update_project_image(image_id: int, image_update: ProjectImageUpdate):
    """Update a project image."""
    # Check if image exists
    existing = await fetch_one("SELECT * FROM project_images WHERE id = %s", (image_id,))
    
    if not existing:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Build the update query dynamically based on provided fields
    update_fields = []
    params = []
    
    if image_update.title is not None:
        update_fields.append("title = %s")
        params.append(image_update.title)
    
    if image_update.description is not None:
        update_fields.append("description = %s")
        params.append(image_update.description)
    
    if image_update.image_url is not None:
        update_fields.append("image_url = %s")
        params.append(image_update.image_url)
    
    if image_update.primary is not None:
        update_fields.append("primary = %s")
        params.append(image_update.primary)
        
        # If setting as primary, update other images to not be primary
        if image_update.primary:
            await execute_query(
                "UPDATE project_images SET primary = false WHERE project_id = %s AND id != %s",
                (existing["project_id"], image_id)
            )
    
    if image_update.order is not None:
        update_fields.append('"order" = %s')
        params.append(image_update.order)
    
    # Update the image if there are fields to update
    if update_fields:
        update_query = f"""
        UPDATE project_images 
        SET {', '.join(update_fields)}
        WHERE id = %s
        """
        
        params.append(image_id)
        await execute_query(update_query, tuple(params))
    
    # Get the updated image
    updated = await fetch_one("SELECT * FROM project_images WHERE id = %s", (image_id,))
    return updated

@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_image(image_id: int):
    """Delete a project image."""
    # Check if image exists
    existing = await fetch_one("SELECT id, image_url FROM project_images WHERE id = %s", (image_id,))
    
    if not existing:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete the image
    await execute_query("DELETE FROM project_images WHERE id = %s", (image_id,))
    
    # TODO: Delete the actual image file from storage (optional)
    
    return JSONResponse(content={}, status_code=status.HTTP_204_NO_CONTENT)
