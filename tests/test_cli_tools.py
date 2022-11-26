from click.testing import CliRunner

from iot_data_receiver.cli_tools import create_sender


def test_create_sender(test_session):
    _, db = test_session

    runner = CliRunner()
    result = runner.invoke(
        create_sender,
        [
            "cli_test_sender",
            "--config_base",
            "config/",
            "--schema",
            "iot_receiver_test",
        ],
    )

    assert result.exit_code == 0

    data = db.query_to_df(
        """
        SELECT *
        FROM senders
        WHERE sender_name = 'cli_test_sender'
        """
    )

    assert len(data) == 1
