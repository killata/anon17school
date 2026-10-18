import os
import sys
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.core.config import settings

engine_kwargs = {
    "echo": False,
    "future": True,
    "pool_pre_ping": True,
}

# If running within a test runner, use NullPool to avoid cross-event-loop connection reuse
is_testing = (
    "pytest" in sys.modules
    or bool(os.getenv("TESTING"))
    or bool(os.getenv("PYTEST_CURRENT_TEST"))
    or any("pytest" in arg for arg in sys.argv)
)

if is_testing:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

# Create asynchronous engine for PostgreSQL using asyncpg
engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)

# Async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection helper for FastAPI and middleware handlers."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
