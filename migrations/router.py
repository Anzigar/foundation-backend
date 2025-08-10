"""
Database migration endpoints for FastAPI application.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import logging
from shared.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/migrations", tags=["migrations"])

@router.post("/standardize-models")
async def run_standardize_models_migration(db: AsyncSession = Depends(get_db)):
    """
    Run the standardize models migration.
    This will:
    1. Check current database schema
    2. Apply the standardization migration
    3. Return the results
    """
    try:
        # First, check current projects table schema
        logger.info("Checking current projects table schema...")
        result = await db.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'projects' 
            ORDER BY ordinal_position
        """))
        
        current_columns = result.fetchall()
        schema_info = []
        for col in current_columns:
            schema_info.append({
                "column": col.column_name,
                "type": col.data_type,
                "nullable": col.is_nullable == 'YES'
            })
        
        logger.info(f"Current projects schema: {schema_info}")
        
        # Check if migration is needed
        has_github_link = any(col["column"] == "github_link" for col in schema_info)
        has_demo_link = any(col["column"] == "demo_link" for col in schema_info)
        has_source_link = any(col["column"] == "source_link" for col in schema_info)
        has_live_link = any(col["column"] == "live_link" for col in schema_info)
        
        migration_needed = (has_github_link or has_demo_link) and not (has_source_link and has_live_link)
        
        if not migration_needed:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Migration not needed - schema is already up to date",
                    "current_schema": schema_info
                }
            )
        
        # Read and execute the migration
        migration_file = Path("migrations/standardize_models.sql")
        if not migration_file.exists():
            raise HTTPException(
                status_code=404, 
                detail="Migration file not found: migrations/standardize_models.sql"
            )
        
        migration_sql = migration_file.read_text()
        logger.info("Executing standardize models migration...")
        
        # Execute the migration
        await db.execute(text(migration_sql))
        await db.commit()
        
        # Verify the migration by checking the schema again
        result = await db.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'projects' 
            ORDER BY ordinal_position
        """))
        
        new_columns = result.fetchall()
        new_schema_info = []
        for col in new_columns:
            new_schema_info.append({
                "column": col.column_name,
                "type": col.data_type,
                "nullable": col.is_nullable == 'YES'
            })
        
        logger.info("Migration completed successfully")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Migration completed successfully",
                "before_migration": schema_info,
                "after_migration": new_schema_info,
                "changes_applied": {
                    "removed_github_specific_fields": has_github_link or has_demo_link,
                    "added_generic_fields": True,
                    "standardized_constraints": True
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Migration failed: {str(e)}"
        )

@router.post("/rename-project-columns")
async def rename_project_columns(db: AsyncSession = Depends(get_db)):
    """
    Specifically rename github_link -> source_link and demo_link -> live_link
    """
    try:
        logger.info("Starting project columns rename migration...")
        
        # Check if old columns exist
        result = await db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'projects' AND column_name IN ('github_link', 'demo_link', 'source_link', 'live_link')
        """))
        
        existing_columns = [row.column_name for row in result.fetchall()]
        
        changes_made = []
        
        # Rename github_link to source_link if needed
        if 'github_link' in existing_columns and 'source_link' not in existing_columns:
            await db.execute(text("ALTER TABLE projects RENAME COLUMN github_link TO source_link"))
            changes_made.append("Renamed github_link to source_link")
            logger.info("Renamed github_link to source_link")
        
        # Rename demo_link to live_link if needed
        if 'demo_link' in existing_columns and 'live_link' not in existing_columns:
            await db.execute(text("ALTER TABLE projects RENAME COLUMN demo_link TO live_link"))
            changes_made.append("Renamed demo_link to live_link")
            logger.info("Renamed demo_link to live_link")
        
        if not changes_made:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "No column renaming needed - columns are already correct",
                    "existing_columns": existing_columns
                }
            )
        
        await db.commit()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Column renaming completed successfully",
                "changes_made": changes_made,
                "existing_columns_before": existing_columns
            }
        )
        
    except Exception as e:
        logger.error(f"Column renaming failed: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Column renaming failed: {str(e)}"
        )

@router.get("/schema-status")
async def check_schema_status(db: AsyncSession = Depends(get_db)):
    """
    Check the current database schema status for all tables.
    """
    try:
        tables = ['projects', 'blog_posts', 'news_articles', 'events']
        schema_status = {}
        
        for table in tables:
            result = await db.execute(text(f"""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                ORDER BY ordinal_position
            """))
            
            columns = []
            for col in result.fetchall():
                columns.append({
                    "name": col.column_name,
                    "type": col.data_type,
                    "nullable": col.is_nullable == 'YES'
                })
            
            schema_status[table] = columns
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "schema_status": schema_status
            }
        )
        
    except Exception as e:
        logger.error(f"Schema check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Schema check failed: {str(e)}"
        )
