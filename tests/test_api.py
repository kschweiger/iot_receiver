from datetime import datetime

import pytest
from data_organizer.db.connection import DatabaseConnection


def test_health(test_session, client):
    response = client.get("/health")
    assert response.status_code == 200


@pytest.mark.parametrize("header", [None, {"access_token": "boguskey"}])
def test_register_invalid_key(test_session, client, header):
    response = client.post("/register", headers=header)
    assert response.status_code == 403


def test_register(test_session, client):
    key, db = test_session
    response = client.post(
        "/register",
        json={"endpoint": "environment", "fields": []},
        headers={"access_token": key},
    )

    assert response.status_code == 200
    assert "Successfully registered" in response.text

    response = client.post(
        "/register",
        json={"endpoint": "environment", "fields": []},
        headers={"access_token": key},
    )

    assert response.status_code == 200
    assert "Endpoint already registered for" in response.text


def get_data(db: DatabaseConnection, table: str, time_stamp: str):
    return db.query_to_df(
        f"""
        SELECT *
        FROM {table}
        WHERE timestamp = '{time_stamp}'
        """
    )


def test_environment(test_environment_session_full, client):
    key, db = test_environment_session_full

    time_stamp = datetime.now().isoformat()
    response = client.post(
        "/environment",
        json={
            "timestamp": [time_stamp],
            "temperature": [1.1],
            "pressure": [2.2],
            "humidity": [3.3],
            "light": [4.4],
            "gas_ox": [5.5],
            "gas_red": [6.6],
            "gas_nh3": [7.7],
        },
        headers={"access_token": key},
    )

    assert response.status_code == 200

    data = get_data(db, "test_name_environment", time_stamp)

    assert not data.empty
