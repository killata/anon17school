from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters.callback_data import CallbackData
from app.db.models.post import PostCategory


class UserCategoryCallback(CallbackData, prefix="user_cat"):
    category: str


def get_user_start_keyboard(mini_app_url: str) -> InlineKeyboardMarkup:
    """Start menu with Mini App launcher and in-bot submission prompt."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎭 Открыть предложку (Mini App)",
                    web_app=WebAppInfo(url=mini_app_url)
                )
            ],
            [
                InlineKeyboardButton(
                    text="✍️ Написать прямо в боте",
                    callback_data="start_direct_post"
                )
            ]
        ]
    )


def get_categories_keyboard() -> InlineKeyboardMarkup:
    """Returns category selection buttons for direct chat posts."""
    buttons = [
        [
            InlineKeyboardButton(
                text="💬 Без тега",
                callback_data=UserCategoryCallback(category="NONE").pack()
            )
        ]
    ]
    buttons.extend([
        [
            InlineKeyboardButton(
                text=f"📌 {cat.value}",
                callback_data=UserCategoryCallback(category=cat.name).pack()
            )
        ]
        for cat in PostCategory
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
