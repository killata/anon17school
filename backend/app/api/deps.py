from datetime import datetime, timezone
from typing import Optional
from fastapi import Header, HTTPException, status, Depends
from aiogram.utils.web_app import safe_parse_webapp_init_data

from app.core.config import settings
from app.core.security import get_author_hash
from app.db.session import get_db
from app.core.redis import get_redis


async def get_current_author_hash(
    authorization: Optional[str] = Header(None),
    x_telegram_init_data: Optional[str] = Header(None),
) -> str:
    """
    Validates HMAC-SHA256 signature of Telegram WebApp initData string.
    
    OpSec Principle:
    1. Extracts telegram user.id purely in memory.
    2. Immediately converts it into an irreversible HMAC-SHA256 author_hash.
    3. Returns ONLY the author_hash to route handlers.
    4. Raw Telegram user ID, username, and first/last name are discarded instantly.
    """
    raw_init_data: Optional[str] = None
    
    if x_telegram_init_data:
        raw_init_data = x_telegram_init_data
    elif authorization:
        if authorization.startswith("tma "):
            raw_init_data = authorization[4:].strip()
        elif authorization.startswith("Bearer "):
            raw_init_data = authorization[7:].strip()
        else:
            raw_init_data = authorization.strip()
            
    if not raw_init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Отсутствуют данные авторизации Telegram WebApp (X-Telegram-Init-Data или Authorization)"
        )
        
    try:
        parsed_data = safe_parse_webapp_init_data(
            token=settings.BOT_TOKEN,
            init_data=raw_init_data
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Недействительная или устаревшая подпись Telegram WebApp: {exc}"
        ) from exc
        
    if not parsed_data.user or not parsed_data.user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Данные пользователя Telegram отсутствуют в WebApp initData"
        )

    # OWASP A07: Anti-Replay Check (сессия не должна быть старше 24 часов)
    if parsed_data.auth_date:
        now_ts = datetime.now(timezone.utc).timestamp()
        auth_ts = parsed_data.auth_date.timestamp() if hasattr(parsed_data.auth_date, "timestamp") else float(parsed_data.auth_date)
        if (now_ts - auth_ts) > 86400:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Сессия Telegram WebApp устарела (старше 24 часов). Пожалуйста, перезапустите приложение."
            )
        
    # Instant cryptographic transformation to irreversible hash
    author_hash = get_author_hash(
        user_id=parsed_data.user.id,
        secret_salt=settings.ANONYMITY_SALT
    )
    
    return author_hash
