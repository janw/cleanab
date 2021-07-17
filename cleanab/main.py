from datetime import date
from datetime import timedelta

import ynab_api as ynab
from fints.client import FinTS3PinTanClient
from logzero import logger

from cleanab.cleaner import FieldCleaner
from cleanab.formatter import print_results
from cleanab.holdings import process_holdings
from cleanab.holdings import retrieve_holdings
from cleanab.transactions import process_transactions
from cleanab.transactions import retrieve_transactions
from cleanab.types import Account
from cleanab.types import AccountType

TODAY = date.today()


def get_ynab_api(config):
    ynab_conf = ynab.Configuration()
    ynab_conf.api_key["Authorization"] = config["ynab"]["access_token"]
    ynab_conf.api_key_prefix["Authorization"] = "Bearer"
    return ynab.TransactionsApi(ynab.ApiClient(ynab_conf))


def get_ynab_account_api(config):
    ynab_conf = ynab.Configuration()
    ynab_conf.api_key["Authorization"] = config["ynab"]["access_token"]
    ynab_conf.api_key_prefix["Authorization"] = "Bearer"
    return ynab.AccountsApi(ynab.ApiClient(ynab_conf))


def process_account(account, accounts_api, budget_id, earliest, cleaner):

    fints = FinTS3PinTanClient(
        account.fints_blz,
        account.fints_username,
        account.fints_password,
        account.fints_endpoint,
    )

    if account.account_type == AccountType.HOLDING:
        holdings = retrieve_holdings(account, fints)

        yield from process_holdings(
            account,
            holdings,
            accounts_api,
            budget_id,
        )
    else:
        transactions = retrieve_transactions(
            account, fints, start_date=earliest, end_date=TODAY
        )
        try:
            existing_transactions = accounts_api.get_transactions(
                budget_id, since_date=earliest
            )
            existing_ids = [
                t.import_id
                for t in existing_transactions.data.transactions
                if t.import_id
            ]
        except Exception:
            logger.warning("Could not retrieve existing transactions")
            existing_ids = []

        yield from process_transactions(
            account,
            transactions,
            cleaner,
            skippable=existing_ids,
        )


def main(dry_run, config, verbose):
    api = get_ynab_api(config)
    accounts_api = get_ynab_account_api(config)
    budget_id = config["ynab"]["budget_id"]

    accounts = [Account(**acc) for acc in config["accounts"]]

    logger.debug("Creating field cleaner instance")
    cleaner = FieldCleaner(
        config.get("pre-replacements", []),
        config.get("replacements", []),
        verbose,
    )

    earliest = max(
        [
            TODAY - timedelta(days=config["timespan"]["maximum_days"]),
            config["timespan"]["$earliest_date__native"],
        ]
    )
    logger.info(f"Checking back until {earliest}")

    processed = []
    for account in accounts:
        logger.info(f"Processing {account}")

        try:
            new_transactions = list(
                process_account(account, accounts_api, budget_id, earliest, cleaner)
            )
            logger.info(f"Got {len(new_transactions)} new transactions")
            processed += new_transactions
        except Exception as exc:
            logger.error("Processing %s failed", account)
            logger.error(str(exc))

    if not dry_run and processed:
        result = api.create_transaction(
            budget_id, ynab.SaveTransactionsWrapper(transactions=processed)
        )
        if verbose:
            print_results(result)
