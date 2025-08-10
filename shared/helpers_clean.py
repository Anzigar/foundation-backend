from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

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
        result = await session.execute(text(query), params)
    else:
        result = await session.execute(text(query))
    
    return [dict(row._mapping) for row in result]

async def fetch_one(query: str, params: Optional[tuple] = None, db: AsyncSession = None) -> Optional[Dict[str, Any]]:
    """Execute a query and fetch one result as dict using SQLAlchemy."""
    if db is None:
        # For standalone function calls, create a session
        from shared.database import async_session
        async with async_session() as session:
            results = await _fetch_with_session(query, params, session)
    else:
        # Use provided session
        results = await _fetch_with_session(query, params, db)
    
    return results[0] if results else None

async def execute_query(query: str, params: Optional[tuple] = None, db: AsyncSession = None) -> int:
    """Execute a query (INSERT, UPDATE, DELETE) and return affected row count."""
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
        result = await session.execute(text(query), params)
    else:
        result = await session.execute(text(query))
    
    await session.commit()
    return result.rowcount
