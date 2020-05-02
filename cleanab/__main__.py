import logging

import logzero

logzero.__name__ = ""
logzero.setup_logger(level=logging.WARNING)

from cleanab.cli import cli  # noqa: F401

cli(auto_envvar_prefix="CLEANAB")
