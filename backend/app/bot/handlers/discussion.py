import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)

router = Router(name="discussion_handler")

# Only process messages from groups and supergroups
router.message.filter(F.chat.type.in_({"group", "supergroup"}))


@router.message(F.is_automatic_forward)
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
    
    comment_text = (
        '💬 <a href="https://t.me/seventeen_confess_bot">Отправить комментарий анонимно</a>'
    )
    
    try:
        await message.reply(
            text=comment_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info(f"Successfully posted anonymous comment link to msg {message.message_id}")
    except Exception as exc:
        logger.error(f"Failed to post comment in discussion group {message.chat.id}: {exc}")
