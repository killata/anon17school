from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BannedHash(Base):
    """
    Blacklist for malicious actors or law-violating authors.
    
    OpSec Principle:
    Stores the author's irreversible HMAC-SHA256 hash.
    Moderators can ban an offender directly from the Telegram moderation group
    without ever knowing their real Telegram account or identity.
    """
    __tablename__ = "banned_hashes"

    author_hash: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        nullable=False,
        comment="Irreversible HMAC-SHA256 author hash"
    )
    
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Legal or policy violation reason"
    )
    
    banned_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Expiration timestamp for temporary bans; NULL indicates permanent ban"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
