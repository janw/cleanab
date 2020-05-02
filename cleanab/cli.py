import click

from cleanab.main import main


@click.command()
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    help="Only fetch and clean up the transactions. None will be added to YNAB.",
)
@click.option(
    "-c",
    "--config",
    "configfile",
    type=click.File("r"),
    default="./config.yaml",
    show_default=True,
    help="Custom location of the config file.",
)
def cli(**kwargs):
    main(**kwargs)
