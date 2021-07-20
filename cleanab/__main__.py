from . import constants
from .cli import cli

cli(auto_envvar_prefix=constants.ENV_PREFIX)
