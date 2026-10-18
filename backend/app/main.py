import asyncio
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
from app.bot.handlers import user_router, admin_router, discussion_router

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
    2. Runs long-polling or registers webhook depending on WEBHOOK_URL.
    3. Shares the same asyncio event loop and connection pools across FastAPI and aiogram.
    4. Handles graceful cleanup of Bot session, Redis pool, and PostgreSQL engine.
    """
    logger.info("Initializing Anon School Bot & API...")
    
    # Регистрация роутеров бота
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(discussion_router)
    
    polling_task = None
    try:
        bot_info = await bot.get_me()
        logger.info(f"Bot connected: @{bot_info.username} (ID: {bot_info.id})")

        if settings.WEBHOOK_URL:
            webhook_url = f"{settings.WEBHOOK_URL.rstrip('/')}/webhook/bot"
            await bot.set_webhook(
                url=webhook_url,
                secret_token=settings.WEBHOOK_SECRET,
                drop_pending_updates=True
            )
            logger.info(f"Telegram Webhook configured: {webhook_url}")
        else:
            logger.info("WEBHOOK_URL is empty. Starting background long-polling for local/dev use...")
            await bot.delete_webhook(drop_pending_updates=False)
            polling_task = asyncio.create_task(dp.start_polling(bot))
    except Exception as exc:
        logger.warning(f"Could not initialize Telegram connection on startup: {exc}")

    yield

    logger.info("Shutting down Anon School Bot & API...")
    if polling_task:
        logger.info("Stopping polling task...")
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass

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

from app.api.v1.posts import router as posts_router

# Монтирование REST API с поддержкой любых префиксов (/api/v1, /api, /v1, /)
app.include_router(api_v1_router, prefix="/api")
app.include_router(api_v1_router, prefix="/v1")
app.include_router(posts_router, prefix="/posts")
app.include_router(posts_router, prefix="/api/posts")


@app.get("/", tags=["health"])
async def root():
    """Корневой эндпоинт для проверки статуса сервиса."""
    return {
        "status": "ok",
        "service": "anon-school-backend",
        "health": "/health",
        "docs": "/docs",
        "message": "Backend API is live. Mini App frontend should be opened via Vercel URL."
    }


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
