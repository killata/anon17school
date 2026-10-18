import html
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core.config import settings
from app.db.models.post import Post
from app.bot.keyboards.admin import get_moderation_keyboard

# Global bot instance
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Global dispatcher instance
dp = Dispatcher()


async def send_post_to_moderation(post: Post, author_short_hash: str) -> int:
    """
    Renders and sends a moderation card to the admin group with 4 action buttons.
    Returns the message ID of the sent card.
    """
    admin_group_id = int(settings.ADMIN_MOD_GROUP_ID) if (
        settings.ADMIN_MOD_GROUP_ID.startswith("-") or settings.ADMIN_MOD_GROUP_ID.isdigit()
    ) else settings.ADMIN_MOD_GROUP_ID
    
    escaped_content = html.escape(post.content)
    caption = (
        f"<b>📨 Новая предложка на модерацию</b>\n\n"
        f"<b>Категория:</b> #{post.category.value}\n"
        f"<b>Автор:</b> <code>#{author_short_hash}</code>\n\n"
        f"{escaped_content}\n\n"
        f"<i>Выберите действие ниже:</i>"
    )
    
    keyboard = get_moderation_keyboard(post.id)
    
    if post.media_file_id:
        msg = await bot.send_photo(
            chat_id=admin_group_id,
            photo=post.media_file_id,
            caption=caption,
            reply_markup=keyboard
        )
    else:
        msg = await bot.send_message(
            chat_id=admin_group_id,
            text=caption,
            reply_markup=keyboard
        )
        
    return msg.message_id
