import html
import uuid
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

from app.core.config import settings
from app.db.session import async_session_maker
from app.db.models.post import Post, PostStatus
from app.db.models.ban import BannedHash
from app.bot.keyboards.admin import ModActionCallback

logger = logging.getLogger(__name__)

router = Router(name="admin_moderation")


@router.callback_query(ModActionCallback.filter())
async def handle_moderation_callback(
    callback: CallbackQuery,
    callback_data: ModActionCallback
):
    """
    Обработчик 4 инлайн-кнопок модерации:
    1. approve    — публикация в основной канал и перевод в APPROVED.
    2. reject     — отклонение и перевод в REJECTED.
    3. reject_law — отклонение за нарушение закона РК.
    4. ban        — занесение author_hash в таблицу banned_hashes.
    """
    post_uuid = uuid.UUID(callback_data.post_id)
    action = callback_data.action

    async with async_session_maker() as session:
        stmt = select(Post).where(Post.id == post_uuid)
        result = await session.execute(stmt)
        post = result.scalar_one_or_none()

        if not post:
            await callback.answer("❌ Ошибка: Пост не найден в базе данных.", show_alert=True)
            return

        author_short = post.author_hash[:6]
        channel_id = int(settings.PUBLIC_CHANNEL_ID) if (
            settings.PUBLIC_CHANNEL_ID.startswith("-") or settings.PUBLIC_CHANNEL_ID.isdigit()
        ) else settings.PUBLIC_CHANNEL_ID

        if action == "approve":
            tag_line = f"<b>#{post.category.value}</b>\n\n" if post.category else ""
            channel_text = (
                f"{tag_line}"
                f"{html.escape(post.content)}\n\n"
                f"<i>—</i>\n"
                f"<i>🎭 Написать анонимно: @seventeen_confess_bot</i>"
            )
            try:
                if post.media_file_id:
                    published = await callback.bot.send_photo(
                        chat_id=channel_id,
                        photo=post.media_file_id,
                        caption=channel_text
                    )
                else:
                    published = await callback.bot.send_message(
                        chat_id=channel_id,
                        text=channel_text
                    )
                post.status = PostStatus.APPROVED
                post.channel_message_id = published.message_id
                await session.commit()

                status_label = f"\n\n<b>✅ ОПУБЛИКОВАНО в канале</b> (Msg ID: {published.message_id})"
                await callback.answer("✅ Пост успешно опубликован!")
            except Exception as exc:
                logger.error(f"Ошибка публикации поста в канал: {exc}")
                await callback.answer(f"❌ Ошибка публикации в канал: {exc}", show_alert=True)
                return

        elif action == "reject":
            post.status = PostStatus.REJECTED
            await session.commit()
            status_label = "\n\n<b>❌ ОТКЛОНЕНО модератором</b>"
            await callback.answer("❌ Пост отклонен.")

        elif action == "reject_law":
            post.status = PostStatus.REJECTED
            await session.commit()
            status_label = "\n\n<b>⚠️ ОТКЛОНЕНО: Нарушение законодательства РК</b>"
            await callback.answer("⚠️ Отклонено (Закон РК).", show_alert=True)

        elif action == "ban":
            post.status = PostStatus.REJECTED
            ban = BannedHash(
                author_hash=post.author_hash,
                reason="Заблокирован администратором из группы модерации"
            )
            session.add(ban)
            await session.commit()
            status_label = f"\n\n<b>🔨 АВТОР ЗАБАНЕН (Хэш: #{author_short})</b>"
            await callback.answer(f"🔨 Автор #{author_short} занесен в черный список!", show_alert=True)

        else:
            await callback.answer("Неизвестное действие")
            return

        # Обновляем текст сообщения в группе модерации и удаляем инлайн-кнопки
        current_text = callback.message.caption or callback.message.text or ""
        updated_text = current_text + status_label

        try:
            if callback.message.photo:
                await callback.message.edit_caption(
                    caption=updated_text,
                    reply_markup=None
                )
            else:
                await callback.message.edit_text(
                    text=updated_text,
                    reply_markup=None
                )
        except Exception as edit_err:
            logger.warning(f"Не удалось обновить сообщение модерации: {edit_err}")
