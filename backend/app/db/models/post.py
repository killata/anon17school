import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, BigInteger, DateTime, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PostCategory(str, enum.Enum):
    OPINION = "Мнение"
    TEACHERS = "Учителя"
    LOOKING_FOR_YOU = "Ищу тебя"
    MEME = "Мем"
    GOSSIP = "Сплетня"


class PostStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


def get_hourly_rounded_utc_now() -> datetime:
    """
    Returns current UTC datetime rounded down to the nearest hour.
    
    OpSec Rationale:
    Exact timestamps (e.g. 14:23:41) allow adversaries to cross-reference
    post creation with class schedules, student attendance records, or school Wi-Fi
    traffic spikes. Rounding to the hour eliminates fine-grained temporal correlation.
    """
    now = datetime.now(timezone.utc)
    return now.replace(minute=0, second=0, microsecond=0)


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # 64-character HMAC-SHA256 author hash (indexed for rate-limiting & duplicate checking)
    author_hash: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    
    category: Mapped[PostCategory | None] = mapped_column(
        Enum(
            PostCategory,
            name="post_category",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=True
    )
    
    # Optional Telegram file_id for attached photos/media
    media_file_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    
    status: Mapped[PostStatus] = mapped_column(
        Enum(
            PostStatus,
            name="post_status",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x]
        ),
        default=PostStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Telegram channel message_id stored after publishing for tracking/takedown/reactions
    channel_message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True
    )
    
    # Rounded to hour for OpSec / TTL cleanup
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_hourly_rounded_utc_now,
        nullable=False
    )

    __table_args__ = (
        Index("idx_posts_author_hash_status", "author_hash", "status"),
    )
