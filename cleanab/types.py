from enum import Enum
from types import SimpleNamespace


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
