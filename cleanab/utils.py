import os
import re
import sys
from functools import lru_cache
from pathlib import Path

from . import constants
from . import schemas

re_wordsplits = re.compile(r"([^\s\-]+(\s|$))")

if sys.platform == "darwin":
    CACHE_HOME = Path("~/Library/Caches").expanduser() / constants.NAME
else:
    CACHE_HOME = (
        Path(os.getenv("XDG_CACHE_HOME", "~/.cache")).expanduser() / constants.NAME
    )


def _replace_capitalize(match):
    return match.group(1).capitalize()


def capitalize_string(string):
    return re_wordsplits.sub(_replace_capitalize, string)


@lru_cache()
def simple_replace_instance(string, replacement=""):
    def replace(x):
        return x.replace(string, replacement), {}

    return replace


@lru_cache()
def regex_sub_instance(*, pattern, repl="", caseinsensitive=True, **kwargs):
    regex = re.compile(
        pattern,
        flags=re.IGNORECASE if caseinsensitive else 0,
    )
    transformers = {
        field: kwargs[f"transform_{field}"]
        for field in schemas.FIELDS_TO_CLEAN_UP
        if f"transform_{field}" in kwargs
    }

    def substitute(x):
        transformed = {}
        for field, template in transformers.items():
            match = regex.match(x)
            if not match:
                continue

            transformed[field] = match.expand(template)

        return regex.sub(repl, x), transformed

    return substitute
