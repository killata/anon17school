import logging
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

from app.core.config import settings
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

router = Router(name="discussion_handler")

# Only process messages from groups and supergroups
router.message.filter(F.chat.type.in_({"group", "supergroup"}))

channel_raw = settings.CHANNEL_ID or settings.PUBLIC_CHANNEL_ID
try:
    target_channel_id = int(channel_raw)
except (ValueError, TypeError):
    target_channel_id = None


@router.message(
    F.is_automatic_forward | (F.forward_from_chat.id == target_channel_id)
)
async def handle_channel_post_forward(message: Message):
    """
    Автоматический комментарий под каждым постом из канала в привязанной группе обсуждений.
    
    Когда пост публикуется в основном канале, Telegram автоматически форвардит его 
    в группу обсуждений с флагом is_automatic_forward=True.
    Бот мгновенно отправляет ответное сообщение-комментарий с гиперссылкой на анонимную отправку.
    """
    logger.info(
        f"Detected auto-forwarded channel post in discussion group {message.chat.id} "
        f"(group_msg_id={message.message_id}, channel_msg_id={message.forward_from_message_id})"
    )

    channel_msg_id = message.forward_from_message_id
    if hasattr(message, "forward_origin") and getattr(message.forward_origin, "message_id", None):
        channel_msg_id = message.forward_origin.message_id

    if channel_msg_id:
        key = f"comment_posted:{channel_msg_id}"
        if not await redis_client.set(key, "1", nx=True, ex=3600):
            logger.info(f"Comment already posted for channel post {channel_msg_id}")
            return

    # Deep-link with target discussion message ID
    deep_link = f"https://t.me/seventeen_confess_bot?start=c_{message.message_id}"
    comment_text = (
        f'💬 <a href="{deep_link}">Отправить комментарий анонимно</a>'
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать комментарий анонимно",
                    url=deep_link
                )
            ]
        ]
    )
    
    try:
        await message.reply(
            text=comment_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info(f"Successfully posted anonymous comment link to msg {message.message_id}")
    except Exception as exc:
        logger.error(f"Failed to post comment in discussion group {message.chat.id}: {exc}")
