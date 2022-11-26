import json
import logging
from typing import Tuple

from data_organizer.config import OrganizerConfig
from data_organizer.db.connection import DatabaseConnection
from data_organizer.db.exceptions import QueryReturnedNoData
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from passlib.context import CryptContext
from pypika import Table
from sqlalchemy import text
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from iot_data_receiver.endpoints import Endpoint
from iot_data_receiver.model import EnvironmentInput, RegisterInput
from iot_data_receiver.utils import get_table_name

FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger("__name__")

app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

api_key_header = APIKeyHeader(name="access_token", auto_error=False)

config = OrganizerConfig(
    name="IoTReceiver",
    config_dir_base="config/",
)


def get_db() -> DatabaseConnection:
    db = DatabaseConnection(**config.settings.db.to_dict(), name="IoTReceiver")
    try:
        yield db
    finally:
        logger.info("Closing DB")
        db.close()


def verify_api_key(plain_api_key, hashed_api_key):
    return pwd_context.verify(plain_api_key, hashed_api_key)


async def get_api_key(
    api_key_header: str = Security(api_key_header), db=Depends(get_db)
) -> Tuple[str, str, int]:
    if api_key_header is None:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="No API Key sent")

    senders = Table("senders")
    try:
        sender_and_keys = db.query(
            db.pypika_query.from_(senders)
            .select(senders.hashed_key, senders.sender_name, senders.id)
            .get_sql()
        )
    except QueryReturnedNoData:
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal database could not be reached",
        )

    for hashed_key, sender_name, sender_id in sender_and_keys:
        if verify_api_key(api_key_header, hashed_key):
            return api_key_header, sender_name, sender_id

    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Could not validate API KEY"
    )


@app.post("/environment")
async def environment(
    environment_input: EnvironmentInput,
    sender: Tuple[str, str, int] = Depends(get_api_key),
    db: DatabaseConnection = Depends(get_db),
):
    endpoint = Endpoint.ENVIRONMENT
    key, sender_name, sender_id = sender

    ers = Table("endpoint_request_subsets")
    try:
        data = db.query(
            db.pypika_query.from_(ers)
            .select(ers.table, ers.subset)
            .where(ers.id == sender_id)
            .where(ers.endpoint == endpoint.value)
            .get_sql()
        )
    except QueryReturnedNoData:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Endpoint not registered"
        )

    table, subset = data[0]
    fields = subset["fields"]

    endpoint_description_cls = endpoint.get_description_class()
    endpoint_description = endpoint_description_cls()

    table_settings = endpoint_description.generate_table_structure(
        get_table_name(sender_name, endpoint.value), fields
    )

    insert_data = []
    environment_input_dict = environment_input.dict()
    for i in range(len(environment_input.timestamp)):
        this_row = []
        for field in fields:
            this_row.append(environment_input_dict[field][i])
        insert_data.append(this_row)

    db.insert(table_settings, insert_data)

    # Load subset defined for the key/endpoint combination
    # Check if the table is present. If not. Create the table
    return {"message": "Received environment data"}


@app.post("/register")
async def register(
    register_input: RegisterInput,
    sender: Tuple[str, str, int] = Depends(get_api_key),
    db: DatabaseConnection = Depends(get_db),
):
    """
    Register a certain endpoint (passed inside the request body) with the passed fileds.
    Valid endpoints are children of the EndpointDescription class.
    A valid call to this function will register the api key as valid key sending data
    to the passed endpoint. Additionally, the corresponding table in the database will
    be created

    :param register_input: Request Model containing the endpoint and the fields send
                           from this api key to the endpoint
    :param sender: API Key for which the endpoint will be registered
    :param db: DatabaseConnection for database interaction
    """
    try:
        endpoint = Endpoint(register_input.endpoint)
    except ValueError:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid endpoint {register_input.endpoint} was passed",
        )

    key, sender_name, sender_id = sender

    ers = Table("endpoint_request_subsets")
    try:
        db.query(
            db.pypika_query.from_(ers)
            .select("*")
            .where(ers.id == sender_id)
            .where(ers.endpoint == register_input.endpoint)
            .get_sql()
        )
    except QueryReturnedNoData:
        pass
    else:
        return {"message": f"Endpoint already registered for user {sender_name}"}

    logger.debug(
        "Found sender name / id  - %s / %s -  for the passed key",
        sender_name,
        sender_id,
    )

    endpoint_description_cls = endpoint.get_description_class()
    endpoint_description = endpoint_description_cls()

    table_settings = endpoint_description.generate_table_structure(
        get_table_name(sender_name, register_input.endpoint), register_input.fields
    )

    db.create_table_from_table_info([table_settings])

    with db.engine.connect() as connection:
        query = (
            db.pypika_query.into(Table("endpoint_request_subsets"))
            .insert(
                sender_id,
                register_input.endpoint,
                get_table_name(sender_name, register_input.endpoint),
                json.dumps(
                    {
                        "fields": endpoint_description.get_final_fields(
                            register_input.fields
                        )
                    }
                ),
            )
            .get_sql()
        )
        logger.debug(query)
        connection.execute(text(query))
        connection.commit()

    logger.info("Added id / endpoint to **endpoint_request_subsets** table")

    response_msg = (
        f"Successfully registered key of user {sender_name} "
        f"for endpoint {register_input.endpoint}"
    )

    return {"message": response_msg}


@app.get("/health")
async def health(db: DatabaseConnection = Depends(get_db)):
    """
    API health check endpoint. Will check if all components are running:
    Checks implemented:
    - Check if the database is reachable
    - Check if the requited tables are present
    """
    # Check if DB is reachable
    if not db.is_valid:
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail="Connection to database could not be established",
        )

    # Check if all required tables are present
    try:
        tables = db.query_to_df(
            text(
                f"""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = '{db.schema}';
                """
            )
        )
    except QueryReturnedNoData:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Not all required tables are present in the database",
        )

    if not all(
        [
            rt in tables.table_name.to_list()
            for rt in ["senders", "endpoint_request_subsets"]
        ]
    ):
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Not all required tables are present in the database",
        )

    return {"message": "All components up and running"}
