from __future__ import annotations

from functools import lru_cache
from multiprocessing import Lock

from fints.client import FinTS3PinTanClient
from logzero import logger

from .models.enums import AccountType

lock = Lock()


def retrieve_transactions(
    sepa_account, fints: FinTS3PinTanClient, *, start_date, end_date
):
    with lock:
        transactions = fints.get_transactions(
            sepa_account, start_date=start_date, end_date=end_date
        )
    return [t.data for t in transactions]


def retrieve_holdings(sepa_account, fints: FinTS3PinTanClient):
    with lock:
        holdings = fints.get_holdings(sepa_account)
    return [{"total_value": h.total_value} for h in holdings]


@lru_cache(maxsize=8)
def get_fints_client(blz, username, password, endpoint):
    logger.info("Retrieving SEPA accounts for %s from %s", username, endpoint)
    fints = FinTS3PinTanClient(blz, username, password, endpoint)
    with lock:
        sepa_accounts = fints.get_sepa_accounts()

    return fints, sepa_accounts


def process_fints_account(account, earliest, latest):
    fints, sepa_accounts = get_fints_client(
        account.fints_blz,
        account.fints_username,
        account.fints_password,
        account.fints_endpoint,
    )
    sepa_account = [acc for acc in sepa_accounts if acc.iban == account.iban][0]

    if account.account_type == AccountType.HOLDING:
        transactions = retrieve_holdings(sepa_account, fints)
    else:
        transactions = retrieve_transactions(
            sepa_account, fints, start_date=earliest, end_date=latest
        )

    return transactions
