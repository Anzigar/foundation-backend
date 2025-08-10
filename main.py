import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles


# Import API routers
from news.router import router as news_router
from events.router import router as events_router
from contacts.router import router as contacts_router
from blog.router import router as blog_router
from api.file_uploads import router as uploads_router
from projects.router import router as projects_router
from migrations.router import router as migrations_router
from auth.router import router as auth_router

# Import the database session dependency instead of get_pool
from shared.database import get_db, create_tables

# Create a simple health check router
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from datetime import datetime
import os

health_router = APIRouter()

@health_router.get("/health")
async def health():
    """Comprehensive health check endpoint."""
    try:
        # Test database connection
        from shared.database import async_session
        
        db_status = "healthy"
        db_error = None
        
        try:
            async with async_session() as session:
                result = await session.execute(text("SELECT 1"))
                if not result.fetchone():
                    db_status = "unhealthy"
                    db_error = "Database query returned no result"
        except Exception as e:
            db_status = "unhealthy"
            db_error = str(e)
        
        health_data = {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "services": {
                "api": "healthy",
                "database": db_status
            }
        }
        
        if db_error:
            health_data["errors"] = {"database": db_error}
            
        # Return 503 if any service is unhealthy
        if db_status == "unhealthy":
            raise HTTPException(status_code=503, detail=health_data)
            
        return health_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

@health_router.get("/")
async def api_root():
    """API root endpoint for health checks and basic info."""
    return {
        "message": "Foundation API",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "news": "/api/news",
            "events": "/api/events", 
            "blog": "/api/blog",
            "projects": "/api/projects",
            "contacts": "/api/contacts",
            "uploads": "/api/uploads",
            "health": "/api/health",
            "docs": "/api/docs"
        }
    }

@health_router.head("/")
async def api_head():
    """Handle HEAD requests to the API root."""
    return {}

app = FastAPI(
    title="Foundation API",
    description="API for the Foundation website",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
    openapi_url="/api/openapi.json"
)



# Custom OpenAPI and Swagger endpoints
@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title=f"{app.title} - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="/static/favicon.png"
    )

@app.get("/api/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.png"
    )

# Custom OpenAPI schema generation
@app.get("/api/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    openapi_schema = get_openapi(
        title="Foundation API",
        version="1.0.0",
        description="API for the Foundation website with detailed documentation",
        routes=app.routes,
        servers=[{"url": "/", "description": "Development server"}]
    )
    
    # Add security schemes if you're using authentication
    openapi_schema["components"] = {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    }
    
    # Apply security globally if needed
    # openapi_schema["security"] = [{"bearerAuth": []}]
    
    return openapi_schema

# GZIP compression middleware for smaller response payloads
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Include routers
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(news_router, prefix="/api/news", tags=["News"])
app.include_router(events_router, prefix="/api/events", tags=["Events"])
app.include_router(contacts_router, prefix="/api/contacts", tags=["Contacts"])
app.include_router(blog_router, prefix="/api/blog", tags=["Blog"])
app.include_router(uploads_router, prefix="/api/uploads", tags=["Uploads"])
app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
app.include_router(migrations_router, prefix="/api", tags=["Migrations"])
# Uncomment these as you create the corresponding modules
# app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Foundation API"}

@app.on_event("startup")
async def startup():
    try:
        # Create database tables if they don't exist
        await create_tables()
        
        # Check database connection on startup
        from sqlalchemy import text
        from shared.database import async_session
        
        # Try to connect to the database and execute a simple query
        async with async_session() as session:
            # Execute a simple test query
            result = await session.execute(text("SELECT 1"))
            if result:
                print("✅ Successfully connected to database")
            else:
                print("⚠️ Database connection test failed")
                
    except Exception as e:
        print(f"⚠️ Warning: Database connection error: {str(e)}")
        print("   Application will start, but database-dependent features won't work.")

if __name__ == "__main__":
    import uvicorn
    import sys
    from pathlib import Path
    
    # Add the project root to Python path if needed
    sys.path.insert(0, str(Path(__file__).parent))
    
    # Using port 5001 instead of 5000 to avoid potential conflicts
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
