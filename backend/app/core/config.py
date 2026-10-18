from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., description="Telegram Bot Token")
    WEBHOOK_SECRET: str = Field(..., description="Webhook secret token")
    PUBLIC_CHANNEL_ID: str = Field(..., description="Public Telegram Channel ID")
    ADMIN_MOD_GROUP_ID: str = Field(..., description="Admin Moderation Group ID")
    ANONYMITY_SALT: str = Field(..., description="Secret salt for irreversible HMAC hashing of user IDs")
    
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/anon_db",
        description="Async PostgreSQL connection URL"
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    MINI_APP_URL: str = Field(
        default="https://your-tunnel-url.trycloudflare.com",
        description="Telegram Mini App Frontend HTTPS URL"
    )
    NEXT_PUBLIC_API_URL: str = Field(
        default="https://your-api-tunnel.trycloudflare.com/api/v1",
        description="Backend API URL"
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
