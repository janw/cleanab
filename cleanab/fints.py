from __future__ import annotations

from multiprocessing import Lock

from fints.client import FinTS3PinTanClient

from cleanab.types import AccountType


lock = Lock()


def get_desired_sepa_account(account, fints: FinTS3PinTanClient):
    with lock:
        sepa_accounts = fints.get_sepa_accounts()
    return [acc for acc in sepa_accounts if acc.iban == account.iban][0]


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


def process_account(account, earliest, latest):
    fints = FinTS3PinTanClient(
        account.fints_blz,
        account.fints_username,
        account.fints_password,
        account.fints_endpoint,
    )
    existing_ids = []

    sepa_account = get_desired_sepa_account(account, fints)

    if account.account_type == AccountType.HOLDING:
        transactions = retrieve_holdings(sepa_account, fints)
    else:
        transactions = retrieve_transactions(
            sepa_account, fints, start_date=earliest, end_date=latest
        )

    return transactions, existing_ids
