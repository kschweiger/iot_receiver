from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Type

from data_organizer.db.model import TableSetting, get_table_setting_from_dict
from pydantic import BaseModel

from iot_data_receiver.model import EnvironmentInput


class Endpoint(str, Enum):
    ENVIRONMENT = "environment"

    def get_description_class(self):
        if self == Endpoint.ENVIRONMENT:
            return EnvironmentEndpointDescription
        else:
            raise NotImplementedError


class EndpointDescription(ABC):
    @abstractmethod
    def get_input_model(self) -> Type[BaseModel]:
        ...

    def get_input_model_properties(self) -> Dict[str, Any]:
        model = self.get_input_model()
        schema = model.schema()
        return schema["properties"]

    def generate_table_structure(
        self, table_name: str, fields: list[str]
    ) -> TableSetting:
        properties = self.get_input_model_properties()
        table_settings_dict: Dict[str, Any] = {"name": table_name}
        for property, items in properties.items():
            if fields and property not in fields:
                continue
            table_settings_dict[property] = {
                "ctype": items["pg_type"],
                "is_primary": items["pg_is_primary"],
                "is_unique": items["pg_is_unique"],
            }
        return get_table_setting_from_dict(table_settings_dict)

    def get_final_fields(self, fields: list[str]) -> list[str]:
        properties = self.get_input_model_properties()
        final_fields = []
        for property, _ in properties.items():
            if fields and property not in fields:
                continue
            final_fields.append(property)

        return final_fields


class EnvironmentEndpointDescription(EndpointDescription):
    def get_input_model(self) -> Type[BaseModel]:
        return EnvironmentInput
