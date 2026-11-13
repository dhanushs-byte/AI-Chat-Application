
import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import Column, Integer, String, DateTime

from app.database import Base


class RateLimitEvent(Base):
    __tablename__ = "rate_limit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)

    api_key_hash = Column(String(64), nullable=False, index=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(
        api_key.encode("utf-8")
    ).hexdigest()


def check_rate_limit(db, api_key: str):

    from app.rate_limit import RateLimitEvent

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=1)

    key_hash = hash_api_key(api_key)

    events = (
        db.query(RateLimitEvent)
        .filter(
            RateLimitEvent.api_key_hash == key_hash,
            RateLimitEvent.created_at >= cutoff
        )
        .order_by(RateLimitEvent.created_at.asc())
        .all()
    )

    import os

    limit = int(os.getenv("MAX_MESSAGES_PER_HOUR", "20"))

    if len(events) >= limit:

        retry_after = max(
            1,
            int(
                (
                    events[0].created_at
                    + timedelta(hours=1)
                    - now
                ).total_seconds()
            )
        )

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)}
        )

    db.add(
        RateLimitEvent(
            api_key_hash=key_hash,
            created_at=now
        )
    )

    db.commit()
