from typing import Dict, Any, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends, Path, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from shared.storage import storage
from shared.database import get_db
from shared.media_models import Media
from shared.media_schemas import MediaUploadResponse, MediaBrowserResponse

router = APIRouter()

@router.post("/upload", response_model=MediaUploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    folder: str = Form("uploads"),
    filename: str = Form(None),
    tags: str = Form(""),
    db: Session = Depends(get_db)
):
    """
    Universal file upload endpoint.
    Returns response matching the MediaBrowser upload payload structure.
    """
    # Validate file
    if not file.content_type:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Determine file type
    file_type = "other"
    if file.content_type.startswith("image/"):
        file_type = "image"
    elif file.content_type.startswith("video/"):
        file_type = "video"
    elif file.content_type.startswith("application/"):
        file_type = "document"
    
    # Upload to S3
    success, message, url = await storage.upload_file(
        file=file,
        folder=folder,
        custom_filename=filename
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Upload failed: {message}")
    
    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
    
    # Create media record
    try:
        file_key = f"{folder}/{filename or file.filename}"
        media = Media(
            name=filename or file.filename,
            file_key=file_key,
            url=url,
            thumbnail_url=url if file_type == "image" else None,
            file_type=file_type,
            file_size=0,  # Could be enhanced to get actual file size
            mime_type=file.content_type,
            tags=tag_list,
            folder=folder
        )
        db.add(media)
        db.commit()
        db.refresh(media)
        
        return MediaUploadResponse(
            id=media.id,
            public_url=url,
            key=file_key,
            name=media.name,
            url=url
        )
    except Exception:
        # Return basic response if database fails
        return MediaUploadResponse(
            id=0,
            public_url=url,
            key=f"{folder}/{filename or file.filename}",
            name=filename or file.filename,
            url=url
        )

@router.delete("/delete")
async def delete_file(url: str, db: Session = Depends(get_db)):
    """Delete a file from S3 storage and database."""
    success, message = storage.delete_file(url)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Delete failed: {message}")
    
    # Remove from database
    try:
        media = db.query(Media).filter(Media.url == url).first()
        if media:
            db.delete(media)
            db.commit()
    except Exception:
        pass  # Continue even if database deletion fails
    
    return {"message": "File deleted successfully"}

@router.get("/browse", response_model=MediaBrowserResponse)
async def browse_media(
    folder: str = Query("", description="Folder to browse"),
    max_items: int = Query(100, ge=1, le=1000, description="Maximum items to return")
):
    """
    Browse media files with structured response for MediaBrowser component.
    """
    success, message, files = storage.list_files(prefix=folder, max_items=max_items)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Browse failed: {message}")
    
    # Define standard folders
    folders = [
        {"name": "Blog Images", "path": "/blog-images"},
        {"name": "Event Photos", "path": "/event-photos"}, 
        {"name": "Project Images", "path": "/project-images"},
        {"name": "Documents", "path": "/documents"}
    ]
    
    # Categorize files
    images = []
    documents = []
    videos = []
    
    for file in files:
        key = file['key'].lower()
        base_name = file['key'].split('/')[-1]
        name = '.'.join(base_name.split('.')[:-1]).replace('-', ' ').replace('_', ' ').title()
        
        if key.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')):
            images.append({
                "key": base_name,
                "name": name,
                "url": file['url'],
                "thumbnail": file['url'],
                "tags": ["featured"] if "featured" in key else []
            })
        elif key.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt')):
            documents.append({
                "key": base_name,
                "name": name,
                "url": file['url']
            })
        elif key.endswith(('.mp4', '.webm', '.mov', '.avi', '.mkv')):
            videos.append({
                "key": base_name,
                "name": name,
                "url": file['url']
            })
    
    return MediaBrowserResponse(
        folders=folders,
        images={"items": images},
        videos={"items": videos},
        documents={"items": documents}
    )

@router.get("/media/{file_key:path}")
async def get_media_url(
    file_key: str = Path(..., description="File key/path in S3"),
    expires_in: int = Query(3600, ge=60, le=86400, description="URL expiration in seconds")
):
    """Generate a pre-signed URL for a file."""
    success, message, url = storage.get_file_url(key=file_key, expires_in=expires_in)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"URL generation failed: {message}")
    
    return {
        "url": url,
        "expires_in": expires_in,
        "key": file_key
    }

@router.get("/list")
async def list_files(
    folder: str = Query("", description="Folder to list files from"),
    max_items: int = Query(100, ge=1, le=1000, description="Maximum items to return")
):
    """List files in a folder."""
    success, message, files = storage.list_files(prefix=folder, max_items=max_items)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"List failed: {message}")
    
    return {
        "items": files,
        "count": len(files),
        "folder": folder
    }
