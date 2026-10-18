import pytest
import asyncio
from datetime import datetime, timezone
from app.core.security import get_author_hash
from app.db.models.post import Post, PostCategory, PostStatus, get_hourly_rounded_utc_now
from app.db.models.ban import BannedHash
from app.db.session import async_session_maker
from sqlalchemy import select


def test_get_author_hash():
    user_id = 123456789
    salt = "test_cryptographic_salt_min_32_chars"
    
    hash1 = get_author_hash(user_id, salt)
    hash2 = get_author_hash(user_id, salt)
    
    assert hash1 == hash2
    assert len(hash1) == 64
    assert isinstance(hash1, str)
    
    # Different user produces different hash
    diff_user_hash = get_author_hash(987654321, salt)
    assert diff_user_hash != hash1
    
    # Different salt produces different hash
    diff_salt_hash = get_author_hash(user_id, "another_salt_value")
    assert diff_salt_hash != hash1


def test_hourly_rounded_utc_now():
    rounded = get_hourly_rounded_utc_now()
    assert rounded.minute == 0
    assert rounded.second == 0
    assert rounded.microsecond == 0
    assert rounded.tzinfo == timezone.utc


@pytest.mark.asyncio
async def test_db_insert_post_and_ban():
    salt = "secret_salt_123"
    author_hash = get_author_hash(555666777, salt)
    
    async with async_session_maker() as session:
        # Create Post
        post = Post(
            author_hash=author_hash,
            content="Тестовое анонимное признание без сохранения ID",
            category=PostCategory.OPINION,
            status=PostStatus.PENDING
        )
        session.add(post)
        await session.commit()
        await session.refresh(post)
        
        assert post.id is not None
        assert post.author_hash == author_hash
        assert post.category == PostCategory.OPINION
        assert post.status == PostStatus.PENDING
        assert post.created_at.minute == 0
        assert post.created_at.second == 0
        
        # Create BannedHash
        ban = BannedHash(
            author_hash=author_hash,
            reason="Violation of RK rules",
            banned_until=None
        )
        session.add(ban)
        await session.commit()
        await session.refresh(ban)
        
        assert ban.author_hash == author_hash
        assert ban.banned_until is None
        
        # Cleanup
        await session.delete(post)
        await session.delete(ban)
        await session.commit()
