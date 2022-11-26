from pathlib import Path

import click
from data_organizer.config import OrganizerConfig
from data_organizer.db.connection import DatabaseConnection
from rich.console import Console

from iot_data_receiver.utils import generate_token

console = Console()


@click.command()
@click.argument("name")
@click.option(
    "--config_base",
    default="config",
    help="Path to the directory containign the configuration files",
)
@click.option(
    "--schema",
    default=None,
    help="Overwrite the schema set in the config",
)
def create_sender(name, config_base, schema):
    exp_config_file_names = ["settings.toml", ".secrets.toml"]
    for config_file in exp_config_file_names:
        if not Path(f"{config_base}/{config_file}").is_file():
            raise RuntimeError("File %s does not exist" % config_file)

    console.print(
        "Creating api-key and database entry for sender "
        f"[underline]{name}[/underline]"
    )

    token, hashed_token = generate_token(20)

    console.print(
        f"Your key is [red bold]{token}[/red bold]. "
        "Save this now, because it can not be reproduced later"
    )

    console.print(f"  Hashed key: [cyan]{hashed_token}[/cyan]")

    config = OrganizerConfig(
        name="IoTKeyCreator",
        config_dir_base=config_base,
    )

    if schema is not None:
        config.settings.db.schema = schema

    with DatabaseConnection(**config.settings.db.to_dict(), name="IoTKeyCreator") as db:
        if not db.has_table(config.tables["senders"].name):
            console.print("Table [i]senders[/i] does not exit")
            return None
        db.insert(config.tables["senders"], [[name, hashed_token]])


if __name__ == "__main__":
    create_sender()
