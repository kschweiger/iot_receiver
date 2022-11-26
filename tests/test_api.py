from copy import deepcopy
from datetime import datetime

import pytest
from data_organizer.db.connection import DatabaseConnection
from dynaconf import LazySettings
from sqlalchemy import text

import iot_data_receiver


def test_health(test_session, client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_invalid_conn(mocker, client):
    settings_: LazySettings = deepcopy(iot_data_receiver.main.config.settings)

    # Set the port to some random bs
    settings_.db.port = "647824"

    mocker.patch.object(iot_data_receiver.main.config, "settings", settings_)

    response = client.get("/health")
    assert response.status_code == 503


@pytest.mark.parametrize(
    "drop_tables",
    [
        ["senders", "endpoint_request_subsets"],
        ["senders"],
        ["endpoint_request_subsets"],
    ],
)
def test_health_missing_tables(test_session, client, drop_tables):
    _, db = test_session
    with db.engine.connect() as connection:
        for table in drop_tables:
            connection.execute(text(f"DROP TABLE {db.schema}.{table};"))
            connection.commit()

    response = client.get("/health")
    assert response.status_code == 500


@pytest.mark.parametrize("header", [None, {"access_token": "boguskey"}])
def test_register_invalid_key(test_session, client, header):
    response = client.post("/register", headers=header)
    assert response.status_code == 403


def test_register_invalid_endpoint(test_session, client):
    key, _ = test_session
    response = client.post(
        "/register",
        headers={"access_token": key},
        json={"endpoint": "bogus_endpoint", "fields": []},
    )
    assert response.status_code == 400


@pytest.mark.parametrize("fields", [[], ["timestamp", "temperature"]])
def test_register(test_session, client, fields):
    key, db = test_session
    response = client.post(
        "/register",
        json={"endpoint": "environment", "fields": fields},
        headers={"access_token": key},
    )

    assert response.status_code == 200
    assert "Successfully registered" in response.text

    response = client.post(
        "/register",
        json={"endpoint": "environment", "fields": fields},
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


def test_environment_minimal(test_environment_session_minimal, client):
    key, db = test_environment_session_minimal

    time_stamp = datetime.now().isoformat()
    response = client.post(
        "/environment",
        json={
            "timestamp": [time_stamp],
            "temperature": [1.1],
        },
        headers={"access_token": key},
    )

    assert response.status_code == 200

    data = get_data(db, "test_name_environment", time_stamp)

    assert not data.empty

    assert (data.columns == ["timestamp", "temperature"]).all()
