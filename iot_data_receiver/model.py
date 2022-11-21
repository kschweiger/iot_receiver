from datetime import datetime

from pydantic import BaseModel


class EnvironmentInput(BaseModel):
    timestamp: list[datetime]
    temperature: list[float]
    pressure: list[float] | None = None
    humidity: list[float] | None = None
    light: list[float] | None = None
    noise: list[float] | None = None
    gas_co: list[float] | None = None
    gas_no2: list[float] | None = None
    gas_nh3: list[float] | None = None


class RegisterInput(BaseModel):
    endpoint: str
    fields: list[str]
