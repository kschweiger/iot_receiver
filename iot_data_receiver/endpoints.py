from abc import ABC, abstractmethod
from enum import Enum
from typing import Type

from pydantic import BaseModel

from iot_data_receiver.model import EnvironmentInput


class Endpoint(str, Enum):
    ENVIRONMENT = "environment"

    def get_class(self):
        if self == Endpoint.ENVIRONMENT:
            return EnvironmentEndpointDescription
        else:
            raise NotImplementedError


class EndpointDescription(ABC):
    @abstractmethod
    def get_input_model(self) -> Type[BaseModel]:
        ...

    def get_input_model_properties(self):
        model = self.get_input_model()
        schema = model.schema()
        return [name for name, _ in schema["properties"]]

    def generate_table_structure(self):
        ...


class EnvironmentEndpointDescription(EndpointDescription):
    def get_input_model(self) -> Type[BaseModel]:
        return EnvironmentInput
