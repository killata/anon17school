import uuid
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class ModActionCallback(CallbackData, prefix="mod"):
    action: str  # "approve", "reject", "reject_law", "ban"
    post_id: str  # UUID as string


def get_moderation_keyboard(post_id: uuid.UUID | str) -> InlineKeyboardMarkup:
    """Returns the 4 required moderation action buttons."""
    pid = str(post_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Опубликовать",
                    callback_data=ModActionCallback(action="approve", post_id=pid).pack()
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=ModActionCallback(action="reject", post_id=pid).pack()
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⚠️ Отклонить (Закон РК)",
                    callback_data=ModActionCallback(action="reject_law", post_id=pid).pack()
                ),
                InlineKeyboardButton(
                    text="🔨 Бан автора",
                    callback_data=ModActionCallback(action="ban", post_id=pid).pack()
                ),
            ]
        ]
    )
