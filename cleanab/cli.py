import logging

import click
import logzero
import yaml

from .schemas import config_validator

logzero.__name__ = "fints"
logzero.setup_logger(level=logging.ERROR)

from cleanab.main import main  # noqa: F401, E402


class ConfigFile(click.File):
    def convert(self, value, param, ctx):
        filename = value
        value = super().convert(value, param, ctx)

        value = yaml.safe_load(value)
        had_errors = False
        for err in config_validator.iter_errors(value):
            if not had_errors:
                click.echo(f"There are issues with your config at {filename}:")
                had_errors = True
            path = " -> ".join((str(p) for p in err.path))
            click.echo(f"\nAt $config -> {path}:\n{err.message}")

        if had_errors:
            raise click.exceptions.Exit(1)
        return value


config_validator


@click.command()
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    help="Only fetch and clean up the transactions. None will be added to YNAB.",
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
    main(**kwargs)
