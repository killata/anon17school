import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from aiogram.types import Update

from app.core.config import settings
from app.core.bot import bot, dp
from app.core.redis import redis_client
from app.db.session import engine
from app.api.v1 import api_v1_router
from app.bot.handlers import user_router, admin_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("anon_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Unified async lifespan:
    1. Registers aiogram routers in the Dispatcher.
    2. Shares the same asyncio event loop and connection pools across FastAPI and aiogram.
    3. Handles graceful cleanup of Bot session, Redis pool, and PostgreSQL engine.
    """
    logger.info("Initializing Anon School Bot & API...")
    
    # Регистрация роутеров бота
    dp.include_router(admin_router)
    dp.include_router(user_router)
    
    # Очистка старых вебхуков или установка нового при наличии домена
    try:
        bot_info = await bot.get_me()
        logger.info(f"Bot connected: @{bot_info.username} (ID: {bot_info.id})")
    except Exception as exc:
        logger.warning(f"Could not reach Telegram Bot API on startup: {exc}")

    yield

    logger.info("Shutting down Anon School Bot & API...")
    await bot.session.close()
    await redis_client.aclose()
    await engine.dispose()
    logger.info("Clean shutdown complete.")


app = FastAPI(
    title="Anonymous School Confessions API & Bot",
    description="Unified async service for Telegram Bot and Next.js Mini App",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS для Telegram WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтирование REST API
app.include_router(api_v1_router, prefix="/api")


@app.post("/webhook/bot", include_in_schema=False)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None)
):
    """
    Telegram Webhook endpoint:
    Валидирует секретный токен заголовка и направляет update в dispatcher aiogram 3.
    """
    if x_telegram_bot_api_secret_token != settings.WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный секретный токен вебхука"
        )
        
    update_data = await request.json()
    update = Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/health", tags=["health"])
async def health_check():
    """Проверка доступности сервиса."""
    return {"status": "ok", "service": "anon-school-backend"}
