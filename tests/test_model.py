from datetime import datetime

import pytest
from pydantic import ValidationError

from iot_data_receiver.model import EnvironmentInput


def test_environment_input_validate_length():
    with pytest.raises(ValidationError):
        EnvironmentInput(
            timestamp=[
                datetime.fromisoformat("2022-01-01T00:01:00"),
                datetime.fromisoformat("2022-01-01T00:02:00"),
            ],
            temperatur=[2.5],
        )
