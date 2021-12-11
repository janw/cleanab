from enum import Enum


class AccountType(str, Enum):
    CHECKING = "checking"
    MASTERCARD = "mastercard"
    HOLDING = "holding"
