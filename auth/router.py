from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import or_
import uuid

from auth.schemas import UserCreate, UserLogin, TokenResponse, UserResponse
from auth.models import User
from auth.utils import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    verify_token,
    create_token_response,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from shared.database import get_db
from shared.helpers import fetch_one, execute_query

router = APIRouter()
security = HTTPBearer()

async def get_user_by_email_or_username(identifier: str) -> Optional[dict]:
    """Get user by email or username."""
    query = """
    SELECT id, full_name, username, email, phone_number, hashed_password, 
           is_active, is_superuser, created_at, updated_at
    FROM auth_users 
    WHERE (email = %s OR username = %s) AND is_active = true
    """
    return await fetch_one(query, (identifier, identifier))

async def get_user_by_username(username: str) -> Optional[dict]:
    """Get user by username."""
    query = """
    SELECT id, full_name, username, email, phone_number, hashed_password, 
           is_active, is_superuser, created_at, updated_at
    FROM auth_users 
    WHERE username = %s AND is_active = true
    """
    return await fetch_one(query, (username,))

async def authenticate_user(email_or_username: str, password: str) -> Optional[dict]:
    """Authenticate user with email/username and password."""
    user = await get_user_by_email_or_username(email_or_username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    username = verify_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.post("/login/", response_model=TokenResponse)
async def login(user_credentials: UserLogin):
    """
    Login endpoint
    
    Accepts either email or username with password.
    Returns JWT token and user information.
    """
    user = await authenticate_user(
        user_credentials.email_or_username, 
        user_credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return create_token_response(type('User', (), user))

@router.post("/register/", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """
    Register new user endpoint
    
    Creates a new user account and returns JWT token with user information.
    Email is auto-generated from username if not provided.
    """
    try:
        # Ensure username is set (auto-generate from email if needed)
        if not user_data.username and user_data.email:
            user_data.username = user_data.email.split('@')[0]
        
        # Check if username already exists
        existing_user = await get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        existing_email = await fetch_one(
            "SELECT id FROM auth_users WHERE email = %s", 
            (user_data.email,)
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user_id = uuid.uuid4()
        hashed_password = get_password_hash(user_data.password)
        
        query = """
        INSERT INTO auth_users (
            id, full_name, username, email, phone_number, hashed_password, 
            is_active, is_superuser
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        await execute_query(query, (
            user_id,
            user_data.full_name,
            user_data.username,
            user_data.email,
            user_data.phone_number,
            hashed_password,
            True,  # is_active
            False  # is_superuser
        ))
        
        # Get the created user
        created_user = await get_user_by_username(user_data.username)
        if not created_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        return create_token_response(type('User', (), created_user))
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the error for debugging
        print(f"Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during registration: {str(e)}"
        )

@router.get("/me/", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse.from_user(type('User', (), current_user))

@router.post("/logout/")
async def logout():
    """
    Logout endpoint
    
    Note: Since we're using stateless JWT tokens, logout is handled on the frontend
    by removing the token from storage. This endpoint exists for consistency.
    """
    return {"message": "Successfully logged out"}
