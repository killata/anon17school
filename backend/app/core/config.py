from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator, field_validator


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., description="Telegram Bot Token")
    WEBHOOK_SECRET: str = Field(default="secret-webhook-token", description="Webhook secret token")
    CHANNEL_ID: str = Field(default="", description="Telegram Channel ID (alias to avoid PUBLIC_ prefix checks)")
    PUBLIC_CHANNEL_ID: str = Field(default="", description="Public Telegram Channel ID")
    ADMIN_MOD_GROUP_ID: str = Field(..., description="Admin Moderation Group ID")
    ANONYMITY_SALT: str = Field(..., description="Secret salt for irreversible HMAC hashing of user IDs")

    @model_validator(mode="after")
    def sync_channel_id(self):
        if not self.PUBLIC_CHANNEL_ID and self.CHANNEL_ID:
            self.PUBLIC_CHANNEL_ID = self.CHANNEL_ID
        elif not self.CHANNEL_ID and self.PUBLIC_CHANNEL_ID:
            self.CHANNEL_ID = self.PUBLIC_CHANNEL_ID
        if not self.PUBLIC_CHANNEL_ID:
            raise ValueError("Either CHANNEL_ID or PUBLIC_CHANNEL_ID must be provided")
        return self
    
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/anon_db",
        description="Async PostgreSQL connection URL"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def sanitize_database_url(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            return v
        v = v.strip()
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[len("postgres://"):]
        elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]
            
        parsed = urlparse(v)
        if parsed.query:
            params = parse_qs(parsed.query)
            if "sslmode" in params:
                ssl_val = params.pop("sslmode")[0]
                if ssl_val in ("require", "verify-ca", "verify-full"):
                    params["ssl"] = ["require"]
            params.pop("channel_binding", None)
            new_query = urlencode({k: val[0] for k, val in params.items()})
            v = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
        elif "neon.tech" in v and "ssl=" not in v:
            v = v + ("&" if "?" in v else "?") + "ssl=require"
            
        return v

    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def sanitize_redis_url(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            return v
        v = v.strip()
        if "redis://" in v and not v.startswith("redis://"):
            idx = v.find("redis://")
            v = v[idx:]
        if "rediss://" in v and not v.startswith("rediss://"):
            idx = v.find("rediss://")
            v = v[idx:]
        if "upstash.io" in v and v.startswith("redis://"):
            v = "rediss://" + v[len("redis://"):]
        return v
    
    MINI_APP_URL: str = Field(
        default="https://your-tunnel-url.trycloudflare.com",
        description="Telegram Mini App Frontend HTTPS URL"
    )
    WEBHOOK_URL: str = Field(
        default="",
        description="Public HTTPS URL for Telegram Webhook (if empty, runs polling)"
    )

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
