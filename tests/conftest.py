
import pytest

from fastapi.testclient import TestClient

from app.main import app

API_KEY = "my_chat_secret_key_123"

HEADERS = {
    "x-api-key": API_KEY
}


@pytest.fixture(autouse=True)
def configure_test_api_key(monkeypatch):
    # Force a predictable API key for automated tests.
    monkeypatch.setenv("API_KEYS", API_KEY)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers():
    return HEADERS.copy()


@pytest.fixture
def test_session(client, auth_headers):

    response = client.post(
        "/sessions",
        headers=auth_headers
    )

    assert response.status_code == 201, (
        f"Session creation failed: {response.status_code} "
        f"{response.text}"
    )

    session_id = response.json()["id"]

    yield session_id

    # Clean up test session.
    client.delete(
        f"/sessions/{session_id}",
        headers=auth_headers
    )

import pytest

from fastapi.testclient import TestClient

from app.main import app

API_KEY = "my_chat_secret_key_123"

HEADERS = {
    "x-api-key": API_KEY
}


@pytest.fixture(autouse=True)
def configure_test_api_key(monkeypatch):
    # Force a predictable API key for automated tests.
    monkeypatch.setenv("API_KEYS", API_KEY)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers():
    return HEADERS.copy()


@pytest.fixture
def test_session(client, auth_headers):

    response = client.post(
        "/sessions",
        headers=auth_headers
    )

    assert response.status_code == 201, (
        f"Session creation failed: {response.status_code} "
        f"{response.text}"
    )

    session_id = response.json()["id"]

    yield session_id

    # Clean up test session.
    client.delete(
        f"/sessions/{session_id}",
        headers=auth_headers
    )
