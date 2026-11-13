
from app.database import SessionLocal
from app.models import Message


def test_create_session(client, auth_headers):

    response = client.post(
        "/sessions",
        headers=auth_headers
    )

    assert response.status_code == 201
    assert "id" in response.json()


def test_session_isolation(
    client,
    auth_headers,
    test_session
):

    response = client.post(
        "/sessions",
        headers=auth_headers
    )

    second_session = response.json()["id"]

    assert test_session != second_session

    # Add a message only to the first session.
    db = SessionLocal()

    try:
        db.add(
            Message(
                session_id=test_session,
                role="user",
                content="Private test message",
                tokens=4
            )
        )
        db.commit()
    finally:
        db.close()

    first = client.get(
        f"/sessions/{test_session}/messages",
        headers=auth_headers
    )

    second = client.get(
        f"/sessions/{second_session}/messages",
        headers=auth_headers
    )

    assert len(first.json()["messages"]) == 1
    assert len(second.json()["messages"]) == 0


def test_delete_session(
    client,
    auth_headers,
    test_session
):

    response = client.delete(
        f"/sessions/{test_session}",
        headers=auth_headers
    )

    assert response.status_code == 204


def test_unknown_session(client, auth_headers):

    response = client.get(
        "/sessions/00000000-0000-0000-0000-000000000001/messages",
        headers=auth_headers
    )

    assert response.status_code == 404
