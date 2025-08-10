"""Deployment validation utilities to prevent duplicate deployments."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from blog.models import BlogPost
from projects.models import Project
from news.models import NewsArticle
from events.models import Event


class DeploymentError(Exception):
    """Custom exception for deployment-related errors."""
    pass


def validate_unique_deployment(
    db: Session,
    content_type: str,
    title: str,
    content_id: Optional[str] = None
) -> None:
    """
    Validate that content with the same title is not already deployed.
    
    Args:
        db: Database session
        content_type: Type of content ('blog', 'project', 'news', 'event')
        title: Title of the content
        content_id: ID of content being updated (optional for updates)
    
    Raises:
        DeploymentError: If content with same title is already deployed
    """
    model_map = {
        'blog': BlogPost,
        'project': Project,
        'news': NewsArticle,
        'event': Event
    }
    
    if content_type not in model_map:
        raise DeploymentError(f"Invalid content type: {content_type}")
    
    model = model_map[content_type]
    
    # Check for existing deployed content with same title
    query = db.query(model).filter(
        model.title == title,
        model.is_deployed == True
    )
    
    # Exclude current content if updating
    if content_id:
        query = query.filter(model.id != content_id)
    
    existing = query.first()
    
    if existing:
        raise DeploymentError(
            f"Content with title '{title}' is already deployed. "
            f"Cannot deploy duplicate {content_type}."
        )


def deploy_content(
    db: Session,
    content_instance: Any,
    force: bool = False
) -> Dict[str, Any]:
    """
    Deploy content with validation and tracking.
    
    Args:
        db: Database session
        content_instance: The content model instance to deploy
        force: Whether to force deployment (bypasses some checks)
    
    Returns:
        Dict with deployment status and information
    
    Raises:
        DeploymentError: If deployment validation fails
    """
    try:
        # Check if already deployed
        if content_instance.is_deployed and not force:
            raise DeploymentError(
                f"Content '{content_instance.title}' is already deployed. "
                "Use force=True to redeploy."
            )
        
        # Validate unique deployment unless forcing
        if not force:
            content_type = content_instance.__tablename__.replace('_', '').replace('s', '')
            if content_type == 'blogpost':
                content_type = 'blog'
            elif content_type == 'newsarticle':
                content_type = 'news'
            
            validate_unique_deployment(
                db, 
                content_type, 
                content_instance.title, 
                str(content_instance.id)
            )
        
        # Update deployment fields
        now = datetime.now(timezone.utc)
        content_instance.is_deployed = True
        content_instance.deployed_at = now
        content_instance.deployment_count = (content_instance.deployment_count or 0) + 1
        
        # Set published status for content types that have it
        if hasattr(content_instance, 'is_published'):
            content_instance.is_published = True
            if not content_instance.published_at:
                content_instance.published_at = now
            content_instance.last_published_at = now
        elif hasattr(content_instance, 'published'):
            content_instance.published = True
        
        db.commit()
        
        return {
            "status": "deployed",
            "deployed_at": now.isoformat(),
            "deployment_count": content_instance.deployment_count,
            "message": f"Content '{content_instance.title}' deployed successfully"
        }
        
    except IntegrityError as e:
        db.rollback()
        if "uq_" in str(e.orig):
            raise DeploymentError(
                "Deployment failed: Content with this title is already deployed"
            )
        raise DeploymentError(f"Database constraint violation: {str(e)}")
    except Exception as e:
        db.rollback()
        raise DeploymentError(f"Deployment failed: {str(e)}")


def undeploy_content(
    db: Session,
    content_instance: Any
) -> Dict[str, Any]:
    """
    Undeploy content by setting deployment status to False.
    
    Args:
        db: Database session
        content_instance: The content model instance to undeploy
    
    Returns:
        Dict with undeployment status and information
    """
    try:
        if not content_instance.is_deployed:
            raise DeploymentError(
                f"Content '{content_instance.title}' is not currently deployed"
            )
        
        # Update deployment fields
        content_instance.is_deployed = False
        content_instance.deployed_at = None
        
        # Note: We keep deployment_count and published status for history
        
        db.commit()
        
        return {
            "status": "undeployed",
            "undeployed_at": datetime.now(timezone.utc).isoformat(),
            "message": f"Content '{content_instance.title}' undeployed successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise DeploymentError(f"Undeployment failed: {str(e)}")


def get_deployment_status(content_instance: Any) -> Dict[str, Any]:
    """
    Get comprehensive deployment status for content.
    
    Args:
        content_instance: The content model instance
    
    Returns:
        Dict with deployment status information
    """
    return {
        "is_deployed": content_instance.is_deployed,
        "deployed_at": content_instance.deployed_at.isoformat() if content_instance.deployed_at else None,
        "deployment_count": content_instance.deployment_count or 0,
        "is_published": getattr(content_instance, 'is_published', None) or getattr(content_instance, 'published', None),
        "published_at": getattr(content_instance, 'published_at', None),
        "can_deploy": not content_instance.is_deployed,
        "title": content_instance.title,
        "slug": content_instance.slug
    }
