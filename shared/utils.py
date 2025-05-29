import re
from typing import Any, Dict, List, Optional
import unicodedata

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
