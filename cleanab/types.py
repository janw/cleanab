from enum import Enum

from .validators import is_iban
from .validators import is_uuid


class AccountType(str, Enum):
    CHECKING = "checking"
    MASTERCARD = "mastercard"
    HOLDING = "holding"


class Account:
    name = ""
    iban = ""
    ynab_id = ""
    cleared = False
    approved = False
    acc_type = AccountType.CHECKING

    fints_username = ""
    fints_password = ""

    def __init__(
        self,
        *,
        iban,
        fints_username,
        fints_password,
        fints_blz,
        fints_endpoint,
        ynab_id,
        account_type=AccountType.CHECKING.name,
        default_cleared=False,
        default_approved=False,
        friendly_name="",
        **kwargs,
    ):
        if not is_iban(iban):
            raise ValueError("iban must be a valid IBAN")
        self.iban = iban

        if not is_uuid(ynab_id):
            raise ValueError("ynab_id must be UUID")
        self.ynab_id = ynab_id

        if not fints_blz.isdigit():
            raise ValueError("fints_blz must be numeric")
        self.fints_blz = fints_blz

        if not fints_endpoint.startswith("https://"):
            raise ValueError("fints_endpoint must be HTTPS URL")
        self.fints_endpoint = fints_endpoint

        self.fints_username = fints_username
        self.fints_password = fints_password

        account_type = account_type.upper()
        account_type_enum = getattr(AccountType, account_type, None)
        if not account_type_enum:
            allowed_vals = ", ".join((e.name for e in AccountType)).lower()
            raise ValueError(f"account_type must be one of {allowed_vals}")
        self.account_type = account_type_enum

        self.default_cleared = "cleared" if default_cleared else "uncleared"
        self.default_approved = default_approved

        self.name = friendly_name

    def __str__(self):
        if self.name:
            return f"{self.acc_type} account {self.name} (…{self.iban[-4:]})"
        return f"{self.acc_type} account {self.iban}"
