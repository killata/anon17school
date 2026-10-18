from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator


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
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
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
