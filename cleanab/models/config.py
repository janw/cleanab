from datetime import date
from typing import Any, List, Union

from pydantic import BaseModel, Extra, confloat, conint, conlist
from pydantic.main import create_model

from ..constants import FIELDS_TO_CLEAN_UP
from .account_config import AccountConfig
from .cleaner import FinalizerDefinition, ReplacementDefinition


class TimespanConfig(BaseModel):
    earliest_date = date(2000, 1, 1)
    maximum_days: conint(ge=1) = 30


class CleanabConfig(BaseModel):
    concurrency: conint(gt=0) = 1
    minimum_holdings_delta: confloat(ge=0) = 1
    debug: bool = False


NestedReplacementEntry = List[Union[ReplacementDefinition, str]]
FullReplacementEntry = List[
    Union[
        NestedReplacementEntry,
        ReplacementDefinition,
        str,
    ]
]

ReplacementFields = create_model(
    "ReplacementFields",
    **{field: (FullReplacementEntry, []) for field in FIELDS_TO_CLEAN_UP}
)


FinalizerFields = create_model(
    "FinalizerFields",
    **{
        field: (FinalizerDefinition, FinalizerDefinition())
        for field in FIELDS_TO_CLEAN_UP
    }
)


class Config(BaseModel):
    cleanab = CleanabConfig()
    timespan = TimespanConfig()
    app_module: str = "cleanab.apps.ynab5"
    app_config: Any
    accounts: conlist(AccountConfig, min_items=1)
    replacements = ReplacementFields()
    pre_replacements = ReplacementFields()
    finalizer = FinalizerFields()

    class Config:
        extra = Extra.allow
