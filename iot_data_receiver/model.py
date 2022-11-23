from datetime import datetime

from pydantic import BaseModel, Field, ValidationError, root_validator


class EnvironmentInput(BaseModel):
    timestamp: list[datetime] = Field(
        alias="timestamp", pg_type="TIMESTAMP", pg_is_primary=True, pg_is_unique=True
    )
    temperature: list[float] = Field(
        alias="temperature", pg_type="FLOAT", pg_is_primary=False, pg_is_unique=False
    )
    pressure: list[float] | None = Field(
        default=None,
        alias="pressure",
        pg_type="FLOAT",
        pg_is_primary=False,
        pg_is_unique=False,
    )
    humidity: list[float] | None = Field(
        default=None,
        alias="humidity",
        pg_type="FLOAT",
        pg_is_primary=False,
        pg_is_unique=False,
    )
    light: list[float] | None = Field(
        default=None,
        alias="light",
        pg_type="FLOAT",
        pg_is_primary=False,
        pg_is_unique=False,
    )
    gas_ox: list[float] | None = Field(
        default=None,
        alias="gas_ox",
        pg_type="FLOAT",
        pg_is_primary=False,
        pg_is_unique=False,
    )
    gas_red: list[float] | None = Field(
        default=None,
        alias="gas_red",
        pg_type="FLOAT",
        pg_is_primary=False,
        pg_is_unique=False,
    )
    gas_nh3: list[float] | None = Field(
        default=None,
        alias="gas_nh3",
        pg_type="FLOAT",
        pg_is_primary=False,
        pg_is_unique=False,
    )

    @root_validator
    def check_list_len(cls, values):
        for field, value in values.items():
            if field == "timestamp":
                continue
            if value is not None:
                if len(value) != len(values["timestamp"]):
                    raise ValidationError
        return values


class RegisterInput(BaseModel):
    endpoint: str
    fields: list[str]
