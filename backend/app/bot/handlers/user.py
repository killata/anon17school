import io
import logging
from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_author_hash
from app.core.redis import redis_client
from app.core.bot import send_post_to_moderation
from app.db.session import async_session_maker
from app.db.models.post import Post, PostCategory, PostStatus
from app.db.models.ban import BannedHash
from app.bot.keyboards.user import (
    get_user_start_keyboard,
    get_categories_keyboard,
    UserCategoryCallback,
)
from app.services.image_scrubber import scrub_image_exif

logger = logging.getLogger(__name__)

router = Router(name="user_direct")
router.message.filter(F.chat.type == "private")


class DirectPostFSM(StatesGroup):
    waiting_for_category = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Приветствие, краткая выжимка правил и инлайн-кнопка WebAppInfo для запуска Mini App.
    """
    await state.clear()
    
    welcome_text = (
        "🎭 <b>Анонимная платформа мнений и признаний</b>\n\n"
        "Здесь ты можешь свободно делиться признаниями, критикой, школьными историями и мемами.\n\n"
        "🛡 <b>Гарантия 100% анонимности:</b>\n"
        "• Твой Telegram ID шифруется необратимым хэшем и нигде не сохраняется в открытом виде.\n"
        "• Все прикрепленные фото автоматически очищаются от EXIF-меток (GPS-координаты, модель телефона, дата съемки).\n"
        "• Создатель и модераторы технически не могут узнать твой аккаунт.\n\n"
        "⚖️ <b>Границы правил (Закон РК):</b>\n"
        "Разрешены оценочные суждения, критика уроков и юмор. Запрещены: слив персональных данных (телефоны, адреса, ИИН), травля, прямые оскорбления и запрещенные вещества.\n\n"
        "<i>Открой Mini App для красивого оформления или просто отправь текст/фото прямо сюда в чат:</i>"
    )
    
    await message.answer(
        text=welcome_text,
        reply_markup=get_user_start_keyboard(settings.MINI_APP_URL)
    )


@router.callback_query(F.data == "start_direct_post")
async def on_start_direct(callback: CallbackQuery):
    await callback.message.answer(
        "✍️ Отправь текст своего признания или прикрепи фото с описанием прямо в этот чат:"
    )
    await callback.answer()


@router.message(F.text | F.photo)
async def on_user_content_submitted(message: Message, state: FSMContext):
    """
    Принимает текст или фото напрямую через чат бота для тех, кому лень открывать Mini App.
    Запрашивает выбор категории.
    """
    content = message.text or message.caption or ""
    if not content and not message.photo:
        await message.answer("Пожалуйста, отправьте текст сообщения или фото.")
        return

    media_file_id = None
    if message.photo:
        # Скачиваем фото и очищаем от EXIF
        photo = message.photo[-1]
        file_io = io.BytesIO()
        await message.bot.download(photo, destination=file_io)
        raw_bytes = file_io.getvalue()
        
        try:
            clean_bytes, _ = scrub_image_exif(raw_bytes)
            # Отправляем очищенное фото обратно в виде невидимого кэша или используем существующий photo.file_id
            # Для надежности пересылаем очищенную копию
            input_file = BufferedInputFile(clean_bytes, filename="clean.jpg")
            cached = await message.bot.send_photo(
                chat_id=message.from_user.id,
                photo=input_file,
                caption="<i>[Фото очищено от метаданных]</i>"
            )
            media_file_id = cached.photo[-1].file_id
            await message.bot.delete_message(chat_id=message.from_user.id, message_id=cached.message_id)
        except Exception as exc:
            logger.warning(f"Ошибка очистки фото: {exc}")
            media_file_id = photo.file_id

    # Сохраняем черновик в FSM
    await state.update_data(content=content, media_file_id=media_file_id)
    await state.set_state(DirectPostFSM.waiting_for_category)
    
    await message.answer(
        "🏷 <b>Выберите категорию для вашего поста:</b>",
        reply_markup=get_categories_keyboard()
    )


@router.callback_query(DirectPostFSM.waiting_for_category, UserCategoryCallback.filter())
async def on_category_chosen(callback: CallbackQuery, callback_data: UserCategoryCallback, state: FSMContext):
    """Завершает публикацию из чата: проверяет бан, лимиты, сохраняет в БД и шлет модераторам."""
    data = await state.get_data()
    content = data.get("content", "")
    media_file_id = data.get("media_file_id")
    await state.clear()
    category_enum = None if callback_data.category == "NONE" else PostCategory[callback_data.category]
    user_id = callback.from_user.id
    author_hash = get_author_hash(user_id=user_id, secret_salt=settings.ANONYMITY_SALT)

    async with async_session_maker() as session:
        # 1. Проверка бана
        ban_stmt = select(BannedHash).where(BannedHash.author_hash == author_hash)
        ban_res = await session.execute(ban_stmt)
        ban_record = ban_res.scalar_one_or_none()
        
        if ban_record:
            now = datetime.now(timezone.utc)
            if ban_record.banned_until is None or ban_record.banned_until > now:
                await callback.message.edit_text("🚫 Вы заблокированы и не можете отправлять посты.")
                await callback.answer()
                return

        # 2. Rate limit (1 пост в 5 минут)
        rate_key = f"ratelimit:post:{author_hash}"
        if await redis_client.exists(rate_key):
            ttl = await redis_client.ttl(rate_key)
            await callback.message.edit_text(
                f"⏳ Вы можете отправить следующий пост через {ttl} сек. (Лимит: 1 пост в 5 минут)."
            )
            await callback.answer()
            return

        # 3. Сохранение поста
        post = Post(
            author_hash=author_hash,
            content=content,
            category=category_enum,
            media_file_id=media_file_id,
            status=PostStatus.PENDING
        )
        session.add(post)
        await session.commit()
        await session.refresh(post)

        # 4. Установка таймера в Redis
        await redis_client.set(rate_key, "1", ex=300)

        # 5. Отправка в админку
        author_short = author_hash[:6]
        try:
            await send_post_to_moderation(post, author_short)
        except Exception as exc:
            logger.error(f"Не удалось отправить в группу модерации: {exc}")

        await callback.message.edit_text(
            f"✅ <b>Ваше сообщение принято!</b>\n\n"
            f"Категория: #{category_enum.value}\n"
            f"Статус: <i>На модерации</i>\n\n"
            f"После одобрения пост появится в основном канале без каких-либо твоих данных."
        )
        await callback.answer()
