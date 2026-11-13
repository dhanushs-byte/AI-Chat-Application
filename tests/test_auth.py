
def test_missing_api_key(client):

    response = client.get("/sessions")

    assert response.status_code == 401


def test_invalid_api_key(client):

    response = client.get(
        "/sessions",
        headers={"x-api-key": "wrong_key"}
    )

    assert response.status_code == 403


def test_valid_api_key(client, auth_headers):

    response = client.get(
        "/sessions",
        headers=auth_headers
    )

    assert response.status_code == 200
