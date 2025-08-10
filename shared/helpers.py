from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

def convert_uuid_params(params: tuple) -> tuple:
    """Convert UUID objects to strings for PostgreSQL compatibility."""
    if not params:
        return params
    
    converted = []
    for param in params:
        if isinstance(param, uuid.UUID):
            converted.append(str(param))
        else:
            converted.append(param)
    return tuple(converted)

def is_uuid_string(value: str) -> bool:
    """Check if a string is a valid UUID format."""
    if not isinstance(value, str) or len(value) != 36:
        return False
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False

def detect_uuid_columns(query: str) -> list:
    """Detect which parameter positions are likely UUID columns based on query."""
    uuid_positions = []
    query_lower = query.lower()
    
    # For INSERT statements into tables with id columns, first param is usually UUID
    if 'insert into' in query_lower and 'values' in query_lower:
        # Check if it's inserting into tables that have UUID id columns
        uuid_tables = ['news_articles', 'blog_posts', 'events', 'projects', 'project_images', 'auth_users']
        for table in uuid_tables:
            if table in query_lower:
                uuid_positions.append(0)  # First parameter is always the id
                break
        
        # Look for other common UUID column patterns in the query
        uuid_column_patterns = ['project_id', 'user_id', 'article_id', 'event_id', 'blog_id']
        for pattern in uuid_column_patterns:
            if pattern in query_lower:
                # This is simplified - in a real implementation you'd parse the column order
                pass
    
    # For WHERE clauses with id conditions
    elif 'where' in query_lower and ('id = %s' in query_lower or 'id=%s' in query_lower):
        # Find position of the id parameter
        uuid_positions.append(0)  # Simplified assumption
    
    return uuid_positions

async def fetch_all(query: str, params: Optional[tuple] = None, db: AsyncSession = None) -> List[Dict[str, Any]]:
    """Execute a query and fetch all results as dicts using SQLAlchemy."""
    if db is None:
        # For standalone function calls, create a session
        from shared.database import async_session
        async with async_session() as session:
            return await _fetch_with_session(query, params, session)
    else:
        # Use provided session
        return await _fetch_with_session(query, params, db)

async def _fetch_with_session(query: str, params: Optional[tuple], session: AsyncSession) -> List[Dict[str, Any]]:
    if params:
        # Detect UUID column positions
        uuid_positions = detect_uuid_columns(query)
        
        # Convert the query to use named parameters and create a parameter dictionary
        param_dict = {}
        modified_query = query
        
        for i, param in enumerate(params):
            param_name = f"param{i+1}"
            
            # Keep UUID values as strings but cast them in SQL
            if i in uuid_positions and isinstance(param, str) and is_uuid_string(param):
                param_dict[param_name] = param  # Keep as string
                # Replace %s with :param_name::uuid for UUID parameters
                modified_query = modified_query.replace('%s', f':{param_name}::uuid', 1)
            elif isinstance(param, uuid.UUID):
                # Convert UUID objects to strings and cast in SQL
                param_dict[param_name] = str(param)
                modified_query = modified_query.replace('%s', f':{param_name}::uuid', 1)
            else:
                param_dict[param_name] = param
                # Replace the first %s with :param_name
                modified_query = modified_query.replace('%s', f':{param_name}', 1)
        
        result = await session.execute(text(modified_query), param_dict)
    else:
        result = await session.execute(text(query))
    
    return [dict(row._mapping) for row in result]

async def fetch_one(query: str, params: Optional[tuple] = None, db: AsyncSession = None) -> Optional[Dict[str, Any]]:
    """Execute a SQL query and fetch one result as dict using SQLAlchemy."""
    results = await fetch_all(query, params, db)
    return results[0] if results else None

async def execute_query(query: str, params: Optional[tuple] = None, db: AsyncSession = None) -> int:
    """Execute a SQL query and return the number of affected rows using SQLAlchemy."""
    if db is None:
        # For standalone function calls, create a session
        from shared.database import async_session
        async with async_session() as session:
            return await _execute_with_session(query, params, session)
    else:
        # Use provided session
        return await _execute_with_session(query, params, db)

async def _execute_with_session(query: str, params: Optional[tuple], session: AsyncSession) -> int:
    if params:
        # Detect UUID column positions
        uuid_positions = detect_uuid_columns(query)
        
        # Convert the query to use named parameters and create a parameter dictionary
        param_dict = {}
        modified_query = query
        
        for i, param in enumerate(params):
            param_name = f"param{i+1}"
            
            # Keep UUID values as strings but cast them in SQL
            if i in uuid_positions and isinstance(param, str) and is_uuid_string(param):
                param_dict[param_name] = param  # Keep as string
                # Replace %s with :param_name::uuid for UUID parameters
                modified_query = modified_query.replace('%s', f':{param_name}::uuid', 1)
            elif isinstance(param, uuid.UUID):
                # Convert UUID objects to strings and cast in SQL
                param_dict[param_name] = str(param)
                modified_query = modified_query.replace('%s', f':{param_name}::uuid', 1)
            else:
                param_dict[param_name] = param
                # Replace the first %s with :param_name
                modified_query = modified_query.replace('%s', f':{param_name}', 1)
        
        result = await session.execute(text(modified_query), param_dict)
    else:
        result = await session.execute(text(query))
    
    await session.commit()
    return result.rowcount
