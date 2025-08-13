import re
from typing import Any, Dict, List, Optional
import unicodedata
import base64
import hashlib
from urllib.parse import quote, unquote

def generate_slug(text: str) -> str:
    """
    Generate a URL-friendly slug from the given text.
    """
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces with hyphens
    text = re.sub(r'[\s]+', '-', text)
    
    # Remove non-alphanumeric characters (except hyphens)
    text = re.sub(r'[^a-z0-9\-]', '', text)
    
    # Remove duplicate hyphens
    text = re.sub(r'\-+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    return text

def format_results_with_metadata(
    items: List[Dict[str, Any]], 
    total_items: int,
    limit: int,
    offset: int
) -> Dict[str, Any]:
    """Format query results with metadata."""
    return {
        "items": items,
        "metadata": {
            "total": total_items,
            "limit": limit,
            "offset": offset,
            "has_more": total_items > (offset + limit)
        }
    }

def encode_s3_path(s3_url: str) -> str:
    """
    Encode S3 URL path for security/obfuscation.
    
    Args:
        s3_url: Full S3 URL (e.g., https://bucket.s3.region.amazonaws.com/path/file.jpg)
        
    Returns:
        Base64 encoded path that can be safely stored and transmitted
    """
    try:
        # Extract just the path part from the S3 URL
        if '.amazonaws.com/' in s3_url:
            path_part = s3_url.split('.amazonaws.com/')[1]
        else:
            # If it's already just a path, use as is
            path_part = s3_url
        
        # Encode the path using base64
        encoded_bytes = base64.urlsafe_b64encode(path_part.encode('utf-8'))
        return encoded_bytes.decode('utf-8')
    except Exception:
        # If encoding fails, return the original URL
        return s3_url

def decode_s3_path(encoded_path: str, bucket_name: str, region: str) -> str:
    """
    Decode the encoded S3 path back to full URL.
    
    Args:
        encoded_path: Base64 encoded path
        bucket_name: S3 bucket name
        region: AWS region
        
    Returns:
        Full S3 URL
    """
    try:
        # Decode the base64 encoded path
        decoded_bytes = base64.urlsafe_b64decode(encoded_path.encode('utf-8'))
        path_part = decoded_bytes.decode('utf-8')
        
        # Reconstruct the full S3 URL
        full_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{path_part}"
        return full_url
    except Exception:
        # If decoding fails, assume it's already a full URL
        return encoded_path

def generate_secure_filename(original_filename: str, prefix: str = "") -> str:
    """
    Generate a secure, unique filename for S3 storage.
    
    Args:
        original_filename: Original filename from upload
        prefix: Optional prefix for the filename
        
    Returns:
        Secure filename with hash and original extension
    """
    import uuid
    import os
    
    # Extract file extension
    _, ext = os.path.splitext(original_filename)
    
    # Generate unique identifier
    unique_id = str(uuid.uuid4())
    
    # Create hash of original filename for additional uniqueness
    filename_hash = hashlib.md5(original_filename.encode()).hexdigest()[:8]
    
    # Combine prefix, hash, unique ID, and extension
    if prefix:
        secure_filename = f"{prefix}_{filename_hash}_{unique_id}{ext}"
    else:
        secure_filename = f"{filename_hash}_{unique_id}{ext}"
    
    return secure_filename
