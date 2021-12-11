import pickle

from pydantic import BaseModel, HttpUrl, constr, validator

from ..utils import CACHE_HOME
from ..validators import is_iban
from .enums import AccountType


class AccountConfig(BaseModel):
    iban: str
    per_app_id: str

    fints_username: str
    fints_password: str
    fints_blz: constr(regex=r"^\d+$")  # noqa: F722
    fints_endpoint: HttpUrl

    friendly_name: str
    account_type: AccountType = AccountType.CHECKING

    default_cleared: bool = False
    default_approved: bool = False

    def __hash__(self):
        return hash(self.iban + self.per_app_id)

    def __eq__(self, other):
        return self.iban == other.iban and self.per_app_id == other.per_app_id

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

    @validator("iban")
    def iban_valid(cls, v):
        if not is_iban(v):
            raise ValueError("Not a valid IBAN")
        return v

    def write_account_cache(self, transactions):
        CACHE_HOME.mkdir(parents=True, exist_ok=True)
        with open(self._account_cache_filename, "wb") as f:
            pickle.dump(transactions, f)

    def read_account_cache(self):
        with open(self._account_cache_filename, "rb") as f:
            return pickle.load(f)
