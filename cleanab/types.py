import pickle
from enum import Enum
from types import SimpleNamespace

from .utils import CACHE_HOME


class StrEnum(str, Enum):
    @classmethod
    def choices(cls):
        return [e.value for e in cls]


class AccountType(StrEnum):
    CHECKING = "checking"
    MASTERCARD = "mastercard"
    HOLDING = "holding"


class Account(SimpleNamespace):
    def __str__(self):
        base = f"{self.account_type.capitalize()} Account"
        if self.friendly_name:
            base += f" '{self.friendly_name}'"
        return base + f" (…{self.iban[-4:]})"

    @property
    def _account_cache_filename(self):
        return CACHE_HOME / f"{self.iban}.pickle"

    @property
    def has_account_cache(self):
        return self._account_cache_filename.is_file()

    def write_account_cache(self, transactions):
        CACHE_HOME.mkdir(parents=True, exist_ok=True)
        with open(self._account_cache_filename, "wb") as f:
            pickle.dump(transactions, f)

    def read_account_cache(self):
        with open(self._account_cache_filename, "rb") as f:
            return pickle.load(f)
