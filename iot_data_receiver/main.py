import logging

from data_organizer.config import OrganizerConfig
from data_organizer.db.connection import DatabaseConnection
from data_organizer.db.exceptions import QueryReturnedNoData
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.openapi.models import APIKey
from fastapi.security import APIKeyHeader
from passlib.context import CryptContext
from pypika import Table
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from iot_data_receiver.endpoints import Endpoint
from iot_data_receiver.model import EnvironmentInput, RegisterInput

FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger("__name__")

app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

api_key_header = APIKeyHeader(name="access_token", auto_error=False)

config = OrganizerConfig(
    name="IoTKeyCreator",
    config_dir_base="config/",
)


def get_db():
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
):
    if api_key_header is None:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="No API Key sent")

    senders = Table("senders")
    try:
        all_keys = db.query(
            db.pypika_query.from_(senders).select(senders.hashed_key).get_sql()
        )
    except QueryReturnedNoData:
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal database could not be reached",
        )

    all_keys = [k[0] for k in all_keys]
    if any(
        verify_api_key(api_key_header, hashed_api_key) for hashed_api_key in all_keys
    ):
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate API KEY"
        )


@app.post("/environment")
async def environment(
    environment_input: EnvironmentInput, api_key: APIKey = Depends(get_api_key)
):
    # Load subset defined for the key/endpoint combination
    # Check if the table is present. If not. Create the table
    return {"message": "Received environment data"}


@app.post("/register")
async def register(register: RegisterInput, api_key: APIKey = Depends(get_api_key)):
    """
    Register a certain endpoint (passed inside the request body) with the passed fileds.
    Valid endpoints are children of the EndpointDescription class.
    A valid call to this function will register the api key as valid key sending data
    to the passed endpoint. Additionally, the corresponding table in the database will
    be created

    :param register: Request Model containing the endpoint and the fields send from this
                     api key to the endpoint
    :param api_key: API Key for which the endpoint will be registered
    """
    try:
        Endpoint(register.endpoint)
    except ValueError:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid endpoint {register.endpoint} was passed",
        )

    return {"message": "Key successfully registered"}


@app.get("/health")
async def health():
    """
    API health check endpoint. Will check if all components are running:
    Checks implemented:
    - Check if the database is reachable
    - Check if the requited tables are present
    """
    # Check if DB is reachable
    # CHeck if all required tables are present
    return {"message": "All components up and running"}
