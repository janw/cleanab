import logging

import logzero

logzero.__name__ = "fints"
logzero.setup_logger(level=logging.ERROR)

from cleanab.cli import cli  # noqa: F401

cli(auto_envvar_prefix="CLEANAB")
