from copy import deepcopy

import pytest
from data_organizer.db.connection import DatabaseConnection
from fastapi.testclient import TestClient
from sqlalchemy import text
from utils import generate_token

import iot_data_receiver
from iot_data_receiver.main import app


@pytest.fixture(scope="session")
def test_session_token(session_mocker):
    settings_ = deepcopy(iot_data_receiver.main.config.settings)

    settings_.db.schema = "iot_receiver_test"
    token, hashed_token = generate_token(20)

    session_mocker.patch.object(iot_data_receiver.main.config, "settings", settings_)

    db = DatabaseConnection(**settings_.db.to_dict(), name="IoTReceiver_test")
    with db.engine.connect() as connection:
        connection.execute(
            text(
                f"""
                CREATE TABLE {settings_.db.schema}.senders (
                    "id" SERIAL PRIMARY KEY,
                    "sender_name" VARCHAR(50) NOT NULL,
                    "hashed_key" TEXT NOT NULL,
                    UNIQUE("hashed_key")
                );
                """
            )
        )
        connection.execute(
            text(
                f"""
                CREATE TABLE {settings_.db.schema}.endpoint_request_subsets (
                    "id" INT NOT NULL,
                    "endpoint" VARCHAR(50) NOT NULL,
                    "table" TEXT NOT NULL,
                    "subset" JSON NOT NULL,
                    FOREIGN KEY("id")
                    REFERENCES {settings_.db.schema}.senders("id")
                )
                """
            )
        )
        connection.execute(
            text(
                f"""
                INSERT INTO {settings_.db.schema}.senders
                VALUES (DEFAULT, 'test_name', '{hashed_token}');
                """
            )
        )
        connection.commit()

    yield token

    with db.engine.connect() as connection:
        connection.execute(text(f"DROP SCHEMA {settings_.db.schema} CASCADE"))
        connection.commit()


@pytest.fixture
def client():
    return TestClient(app)
