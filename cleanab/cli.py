import logging

import click
import logzero
import yaml

from .models.config import Config

logzero.__name__ = "fints"
logzero.setup_logger(level=logging.ERROR)

from cleanab.main import Cleanab  # noqa: F401, E402


class ConfigFile(click.File):
    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)
        value = yaml.safe_load(value)
        return Config.parse_obj(value)


@click.command()
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    help=(
        "Only fetch and clean up the transactions. None will be added in your budgeting"
        " app."
    ),
)
@click.option(
    "-t",
    "--test",
    is_flag=True,
    help=(
        "Testing mode: Fetch transactions and clean them up. The raw transaction data"
        " will be written to disk, so on subsequent --test runs the local copy of the"
        " transaction data will be used. This avoids querying the bank APIs too often."
        " No transaction will be added to in your budgeting app. (implies --dry-run and"
        " --verbose)"
    ),
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show replacements made to the received data",
)
@click.option(
    "-c",
    "--config",
    "config",
    type=ConfigFile("r"),
    default="./config.yaml",
    show_default=True,
    help="Custom location of the config file.",
    metavar="configfile",
)
def cli(**kwargs):
    c = Cleanab(**kwargs)
    c.setup()
    c.run()
