import logging

import logzero

logzero.__name__ = ""
logzero.setup_logger(level=logging.WARNING)

from cleanab.main import main  # noqa: F401

main()
