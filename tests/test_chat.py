
from types import SimpleNamespace

from app.database import SessionLocal
from app.models import Message


def test_mocked_streaming_reply(
    client,
    auth_headers,
    test_session,
    monkeypatch
):

    def fake_stream(messages):

        # First chunk
        yield SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(
                        content="Hello "
                    )
                )
            ],
            usage=None
        )

        # Second chunk
        yield SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(
                        content="from AI!"
                    )
                )
            ],
            usage=None
        )

        # Final usage chunk
        yield SimpleNamespace(
            choices=[],
            usage=SimpleNamespace(
                prompt_tokens=10,
                completion_tokens=5
            )
        )

    monkeypatch.setattr(
        "app.routes.create_stream",
        fake_stream
    )

    response = client.post(
        f"/sessions/{test_session}/chat",
        headers=auth_headers,
        json={
            "message": "Say hello"
        }
    )

    assert response.status_code == 200

    assert "Hello " in response.text
    assert "from AI!" in response.text

    assert '"type": "done"' in response.text


def test_chat_message_persistence(
    client,
    auth_headers,
    test_session,
    monkeypatch
):

    def fake_stream(messages):

        yield SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(
                        content="Mock answer"
                    )
                )
            ],
            usage=None
        )

        yield SimpleNamespace(
            choices=[],
            usage=SimpleNamespace(
                prompt_tokens=10,
                completion_tokens=3
            )
        )

    monkeypatch.setattr(
        "app.routes.create_stream",
        fake_stream
    )

    client.post(
        f"/sessions/{test_session}/chat",
        headers=auth_headers,
        json={"message": "Test persistence"}
    )

    db = SessionLocal()

    try:
        saved = (
            db.query(Message)
            .filter(
                Message.session_id == test_session
            )
            .order_by(Message.id.asc())
            .all()
        )

        assert len(saved) == 2

        assert saved[0].role == "user"
        assert saved[1].role == "assistant"

        assert saved[1].content == "Mock answer"

    finally:
        db.close()
