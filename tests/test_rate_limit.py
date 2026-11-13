
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.rate_limit import RateLimitEvent, hash_api_key


def test_rate_limit_exceeded(
    client,
    auth_headers,
    test_session
):

    key_hash = hash_api_key(
        auth_headers["x-api-key"]
    )

    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        for _ in range(20):
            db.add(
                RateLimitEvent(
                    api_key_hash=key_hash,
                    created_at=now - timedelta(minutes=5)
                )
            )

        db.commit()

        response = client.post(
            f"/sessions/{test_session}/chat",
            headers=auth_headers,
            json={"message": "Rate limit test"}
        )

        assert response.status_code == 429

        assert response.json() == {
            "detail": "Rate limit exceeded"
        }

        assert "Retry-After" in response.headers

    finally:
        db.query(RateLimitEvent).filter(
            RateLimitEvent.api_key_hash == key_hash
        ).delete(synchronize_session=False)

        db.commit()
        db.close()
