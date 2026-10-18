from typing import AsyncGenerator
import redis.asyncio as aioredis
from app.core.config import settings

# Global async Redis pool
redis_client = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Dependency injection helper for FastAPI endpoints."""
    yield redis_client
