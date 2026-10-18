import io
import uuid
import hmac
import hashlib
import urllib.parse
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient, ASGITransport
from PIL import Image
from sqlalchemy import select

from app.main import app
from app.core.config import settings
from app.core.security import get_author_hash
from app.services.image_scrubber import scrub_image_exif
from app.db.models.post import Post, PostCategory, PostStatus
from app.db.models.ban import BannedHash
from app.db.session import async_session_maker
from app.core.redis import redis_client
from app.bot.keyboards.admin import ModActionCallback
from app.bot.handlers.admin import handle_moderation_callback
from unittest.mock import AsyncMock, MagicMock


def generate_valid_webapp_init_data(user_id: int, bot_token: str) -> str:
    """Helper to generate cryptographically valid Telegram WebApp initData string."""
    data = {
        "auth_date": str(int(datetime.now(timezone.utc).timestamp())),
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        "user": f'{{"id":{user_id},"first_name":"Ivan","last_name":"Ivanov","username":"ivan_test"}}'
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    data["hash"] = hash_value
    return urllib.parse.urlencode(data)


def test_exif_scrubbing():
    # Create test image with fake camera EXIF
    im = Image.new("RGB", (80, 80), color="green")
    exif = im.getexif()
    exif[0x0110] = "iPhone 16 Pro Max"
    exif[0x010F] = "Apple"
    raw_buf = io.BytesIO()
    im.save(raw_buf, format="JPEG", exif=exif)
    raw_bytes = raw_buf.getvalue()
    
    # Verify original has tags
    orig_check = Image.open(io.BytesIO(raw_bytes))
    assert len(orig_check.getexif()) > 0
    
    # Scrub
    clean_bytes, mime = scrub_image_exif(raw_bytes)
    assert mime == "image/jpeg"
    
    # Verify scrubbed has ZERO EXIF tags
    clean_check = Image.open(io.BytesIO(clean_bytes))
    assert len(clean_check.getexif()) == 0


@pytest.mark.asyncio
async def test_submit_post_flow():
    test_user_id = 998877665
    init_data = generate_valid_webapp_init_data(test_user_id, settings.BOT_TOKEN)
    expected_hash = get_author_hash(test_user_id, settings.ANONYMITY_SALT)
    
    # Clear rate limit if left from previous runs
    await redis_client.delete(f"ratelimit:post:{expected_hash}")
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Health check
        health_resp = await ac.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "ok"
        
        # 2. Submit post with valid initData
        headers = {"Authorization": f"tma {init_data}"}
        payload = {
            "content": "Учитель физики сегодня очень круто объяснил тему гравитации!",
            "category": "Учителя"
        }
        resp = await ac.post("/api/v1/posts/submit", json=payload, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["category"] == "Учителя"
        assert data["status"] == "PENDING"
        assert data["author_short_hash"] == f"#{expected_hash[:6]}"
        post_id = uuid.UUID(data["id"])
        
        # Verify in DB
        async with async_session_maker() as session:
            db_post = await session.get(Post, post_id)
            assert db_post is not None
            assert db_post.author_hash == expected_hash
            assert db_post.status == PostStatus.PENDING
            
            # 3. Test Rate Limit: immediate second post should return 429
            second_resp = await ac.post("/api/v1/posts/submit", json=payload, headers=headers)
            assert second_resp.status_code == 429
            assert "Слишком частые публикации" in second_resp.json()["detail"]
            
            # 4. Test Ban Check: ban this author_hash
            ban = BannedHash(
                author_hash=expected_hash,
                reason="Тестовый бан"
            )
            session.add(ban)
            await session.commit()
            
            # Delete rate limit to test ban priority
            await redis_client.delete(f"ratelimit:post:{expected_hash}")
            
            banned_resp = await ac.post("/api/v1/posts/submit", json=payload, headers=headers)
            assert banned_resp.status_code == 403
            assert "Вы заблокированы" in banned_resp.json()["detail"]
            
            # Cleanup test records
            await session.delete(ban)
            await session.delete(db_post)
            await session.commit()
        
        await redis_client.delete(f"ratelimit:post:{expected_hash}")


@pytest.mark.asyncio
async def test_invalid_init_data():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"Authorization": "tma invalid_fake_init_data"}
        payload = {"content": "Test text", "category": "Мнение"}
        resp = await ac.post("/api/v1/posts/submit", json=payload, headers=headers)
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_moderation_callback_actions():
    author_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    
    async with async_session_maker() as session:
        post = Post(
            author_hash=author_hash,
            content="Сообщение для тестирования модерации",
            category=PostCategory.MEME,
            status=PostStatus.PENDING
        )
        session.add(post)
        await session.commit()
        await session.refresh(post)
        post_id = post.id
        
        # 1. Test Unauthorized Attempt (OWASP A01 verification)
        unauth_callback = AsyncMock()
        unauth_callback.from_user.id = 999999999
        unauth_callback.message.chat.id = 999999999
        unauth_cb_data = ModActionCallback(action="reject", post_id=str(post_id))
        await handle_moderation_callback(unauth_callback, unauth_cb_data)
        await session.refresh(post)
        assert post.status == PostStatus.PENDING  # Must remain PENDING
        unauth_callback.answer.assert_called_with("⛔ Доступ запрещен. Вы не являетесь модератором.", show_alert=True)

        # 2. Mock Callback for REJECT by authorized moderator
        mock_callback = AsyncMock()
        admin_id = int(settings.ADMIN_MOD_GROUP_ID)
        mock_callback.from_user.id = admin_id
        mock_callback.message.chat.id = admin_id
        mock_callback.message.caption = None
        mock_callback.message.text = "Карточка поста"
        mock_callback.message.photo = None
        mock_callback.bot = AsyncMock()
        
        cb_data = ModActionCallback(action="reject", post_id=str(post_id))
        await handle_moderation_callback(mock_callback, cb_data)
        
        await session.refresh(post)
        assert post.status == PostStatus.REJECTED
        mock_callback.answer.assert_called_with("❌ Пост отклонен.")
        
        # 2. Mock Callback for BAN
        ban_cb_data = ModActionCallback(action="ban", post_id=str(post_id))
        await handle_moderation_callback(mock_callback, ban_cb_data)
        
        ban_res = await session.execute(select(BannedHash).where(BannedHash.author_hash == author_hash))
        ban_record = ban_res.scalar_one_or_none()
        assert ban_record is not None
        assert ban_record.author_hash == author_hash
        
        # Cleanup
        await session.delete(ban_record)
        await session.delete(post)
        await session.commit()
