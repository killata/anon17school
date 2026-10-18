import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from aiogram.types import BufferedInputFile

from app.api.deps import get_current_author_hash
from app.db.session import get_db
from app.core.redis import get_redis
from app.db.models.post import Post, PostCategory, PostStatus
from app.db.models.ban import BannedHash
from app.core.bot import bot, send_post_to_moderation
from app.core.config import settings
from app.services.image_scrubber import scrub_image_exif

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/posts", tags=["posts"])


class PostCreate(BaseModel):
    content: str = Field(..., min_length=3, max_length=4000, description="Текст поста")
    category: Optional[PostCategory] = Field(None, description="Категория поста (опционально)")
    media_file_id: Optional[str] = Field(None, description="Telegram file_id очищенного медиа")


class PostResponse(BaseModel):
    id: uuid.UUID
    category: Optional[PostCategory] = None
    status: PostStatus
    author_short_hash: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.post(
    "/submit",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Отправить анонимное сообщение на модерацию"
)
async def submit_post(
    payload: PostCreate,
    author_hash: str = Depends(get_current_author_hash),
    db: AsyncSession = Depends(get_db),
    redis_conn: aioredis.Redis = Depends(get_redis)
):
    """
    Принимает текст и категорию из Telegram Mini App.
    1. Проверяет наличие автора в черном списке (banned_hashes).
    2. Проверяет Rate Limit в Redis (1 пост в 5 минут).
    3. Сохраняет пост со статусом PENDING.
    4. Отправляет карточку на модерацию в админ-группу.
    """
    # 1. Проверка черного списка
    ban_stmt = select(BannedHash).where(BannedHash.author_hash == author_hash)
    ban_res = await db.execute(ban_stmt)
    ban_record = ban_res.scalar_one_or_none()
    
    if ban_record:
        now = datetime.now(timezone.utc)
        if ban_record.banned_until is None or ban_record.banned_until > now:
            reason = ban_record.reason or "Нарушение правил сообщества"
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Вы заблокированы в предложке. Причина: {reason}"
            )

    # 2. Rate Limiting в Redis (1 пост в 300 секунд на author_hash)
    rate_key = f"ratelimit:post:{author_hash}"
    if await redis_conn.exists(rate_key):
        ttl = await redis_conn.ttl(rate_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Слишком частые публикации. Вы можете отправить следующий пост через {ttl} сек."
        )

    # 3. Сохранение поста со статусом PENDING
    post = Post(
        author_hash=author_hash,
        content=payload.content,
        category=payload.category,
        media_file_id=payload.media_file_id,
        status=PostStatus.PENDING
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    # Устанавливаем кулдаун 5 минут
    await redis_conn.set(rate_key, "1", ex=300)

    # 4. Отправка карточки в группу модерации
    author_short_hash = author_hash[:6]
    try:
        await send_post_to_moderation(post, author_short_hash)
    except Exception as exc:
        logger.error(f"Не удалось отправить пост {post.id} в группу модерации: {exc}")

    return PostResponse(
        id=post.id,
        category=post.category,
        status=post.status,
        author_short_hash=f"#{author_short_hash}",
        created_at=post.created_at
    )


@router.post(
    "/upload-media",
    summary="Очистить фото от EXIF метаданных и получить telegram file_id"
)
async def upload_media(
    file: UploadFile = File(...),
    author_hash: str = Depends(get_current_author_hash)
):
    """
    Принимает изображение, очищает EXIF-теги (GPS, устройство, время) через Pillow
    и регистрирует очищенный файл в Telegram через бота.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только файлы изображений (JPEG, PNG)"
        )
        
    raw_bytes = await file.read()
    if len(raw_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Максимальный размер фото 10 МБ"
        )
        
    try:
        clean_bytes, mime = scrub_image_exif(raw_bytes)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка обработки изображения: {exc}"
        ) from exc
        
    admin_group_id = int(settings.ADMIN_MOD_GROUP_ID) if (
        settings.ADMIN_MOD_GROUP_ID.startswith("-") or settings.ADMIN_MOD_GROUP_ID.isdigit()
    ) else settings.ADMIN_MOD_GROUP_ID

    input_file = BufferedInputFile(clean_bytes, filename="cleaned_image.jpg")
    try:
        # Отправляем фото во временный чат / группу для генерации постоянного Telegram file_id
        sent_msg = await bot.send_photo(
            chat_id=admin_group_id,
            photo=input_file,
            caption="<i>[Системный кэш медиа без EXIF]</i>"
        )
        file_id = sent_msg.photo[-1].file_id
        # Удаляем системное сообщение
        await bot.delete_message(chat_id=admin_group_id, message_id=sent_msg.message_id)
        return {"file_id": file_id}
    except Exception as exc:
        logger.warning(f"Ошибка загрузки фото в Telegram: {exc}")
        # Если группа недоступна, возвращаем сообщение об ошибке
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Не удалось зарегистрировать медиа в Telegram: {exc}"
        ) from exc
