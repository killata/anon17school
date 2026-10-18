from typing import AsyncGenerator
import certifi
import redis.asyncio as aioredis
from app.core.config import settings

redis_kwargs = {
    "encoding": "utf-8",
    "decode_responses": True,
}

# If using TLS encrypted Redis (e.g. Upstash rediss://), inject verified root CA certificates
if settings.REDIS_URL.startswith("rediss://"):
    redis_kwargs["ssl_ca_certs"] = certifi.where()

# Global async Redis pool
redis_client = aioredis.from_url(
    settings.REDIS_URL,
    **redis_kwargs
)


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Dependency injection helper for FastAPI endpoints."""
    yield redis_client
