import pytest
from data_organizer.db.model import TableSetting

from iot_data_receiver.endpoints import EnvironmentEndpointDescription


@pytest.mark.parametrize("fields", [[], ["field_1", "field_3"]])
def test_generate_table_structure(mocker, fields):
    ed = EnvironmentEndpointDescription()

    properties = {
        "field_1": {
            "pg_type": "TIMESTAMP",
            "pg_is_primary": True,
            "pg_is_unique": True,
        },
        "field_2": {
            "pg_type": "INT",
            "pg_is_primary": False,
            "pg_is_unique": False,
        },
        "field_3": {
            "pg_type": "FLOAT",
            "pg_is_primary": False,
            "pg_is_unique": False,
        },
    }

    mocker.patch.object(
        ed,
        "get_input_model_properties",
        return_value=properties,
    )

    ts = ed.generate_table_structure("test_table", fields=fields)

    assert isinstance(ts, TableSetting)
    assert ts.name == "test_table"
    if fields:
        assert set([c.name for c in ts.columns]) == set(fields)
    else:
        assert len(ts.columns) == len(properties.keys())

    for column in ts.columns:
        assert column.ctype == properties[column.name]["pg_type"]
        assert column.is_primary == properties[column.name]["pg_is_primary"]
        assert column.is_unique == properties[column.name]["pg_is_unique"]
