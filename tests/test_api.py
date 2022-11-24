import pytest


def test_health(test_session_token, client):
    response = client.get("/health")
    assert response.status_code == 200


@pytest.mark.parametrize("header", [None, {"access_token": "boguskey"}])
def test_register_invalid_key(test_session_token, client, header):
    response = client.post("/register", headers=header)
    assert response.status_code == 403


def test_register(test_session_token, client):
    response = client.post(
        "/register",
        json={"endpoint": "environment", "fields": []},
        headers={"access_token": test_session_token},
    )

    assert response.status_code == 200
