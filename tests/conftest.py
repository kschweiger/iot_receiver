from copy import deepcopy

import pytest
from data_organizer.db.connection import DatabaseConnection
from dynaconf import LazySettings
from fastapi.testclient import TestClient
from sqlalchemy import text

import iot_data_receiver
from iot_data_receiver.main import app
from iot_data_receiver.utils import generate_token


def setup_database(
    db: DatabaseConnection,
    settings_: LazySettings,
    hashed_token: str,
):
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


def drop_schema(db: DatabaseConnection, schema: str):
    with db.engine.connect() as connection:
        connection.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        connection.commit()


def mock_settings(mocker):
    settings_: LazySettings = deepcopy(iot_data_receiver.main.config.settings)

    settings_.db.schema = "iot_receiver_test"

    mocker.patch.object(iot_data_receiver.main.config, "settings", settings_)

    return settings_


@pytest.fixture
def test_session(mocker):
    settings_ = mock_settings(mocker)

    token, hashed_token = generate_token(20)

    db = DatabaseConnection(**settings_.db.to_dict(), name="IoTReceiver_test")
    setup_database(db, settings_, hashed_token)

    yield token, db

    drop_schema(db, settings_.db.schema)


@pytest.fixture
def test_environment_session_full(mocker):
    settings_ = mock_settings(mocker)

    token, hashed_token = generate_token(20)

    db = DatabaseConnection(**settings_.db.to_dict(), name="IoTReceiver_test")
    setup_database(db, settings_, hashed_token)

    with db.engine.connect() as connection:
        table_name = "test_name_environment"
        connection.execute(
            text(
                """
                INSERT INTO %s.endpoint_request_subsets
                VALUES (
                    1,
                    'environment',
                    '%s',
                    '{"fields": ["timestamp", "temperature", "pressure", "humidity",
                                 "light", "gas_ox", "gas_red", "gas_nh3"]}'
                );
                """
                % (settings_.db.schema, table_name)
            )
        )
        connection.execute(
            text(
                f"""
                CREATE TABLE {settings_.db.schema}.test_name_environment (
                    timestamp timestamp without time zone PRIMARY KEY,
                    temperature double precision NOT NULL,
                    pressure double precision NOT NULL,
                    humidity double precision NOT NULL,
                    light double precision NOT NULL,
                    gas_ox double precision NOT NULL,
                    gas_red double precision NOT NULL,
                    gas_nh3 double precision NOT NULL
                );
                """
            )
        )
        connection.commit()

    yield token, db

    drop_schema(db, settings_.db.schema)


@pytest.fixture
def test_registered_session(mocker):
    settings_ = mock_settings(mocker)

    token, hashed_token = generate_token(20)

    db = DatabaseConnection(
        **settings_.db.to_dict(), name="IoTReceiver_registered_test"
    )
    setup_database(db, settings_, hashed_token)

    yield token

    drop_schema(db, settings_.db.schema)


@pytest.fixture
def client():
    return TestClient(app)
