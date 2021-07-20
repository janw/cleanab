from datetime import date
from datetime import timedelta

import ynab_api as ynab
from fints.client import FinTS3PinTanClient
from logzero import logger

from cleanab.cleaner import FieldCleaner
from cleanab.formatter import print_results
from cleanab.holdings import process_holdings
from cleanab.holdings import retrieve_holdings
from cleanab.transactions import process_account_transactions
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


def process_account(account, accounts_api, budget_id, earliest):

    fints = FinTS3PinTanClient(
        account.fints_blz,
        account.fints_username,
        account.fints_password,
        account.fints_endpoint,
    )
    existing_ids = []

    if account.account_type == AccountType.HOLDING:
        transactions = retrieve_holdings(account, fints)
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

    return transactions, existing_ids


def main(dry_run, test, config, verbose):

    if test:
        dry_run = True
        verbose = True

    api = get_ynab_api(config)
    accounts_api = get_ynab_account_api(config)
    budget_id = config["ynab"]["budget_id"]

    accounts = [Account(**acc) for acc in config["accounts"]]
    logger.debug("Creating field cleaner instance")
    cleaner = FieldCleaner(
        config.get("replacements", []),
        config["finalizer"],
        verbose,
    )

    earliest = max(
        [
            TODAY - timedelta(days=config["timespan"]["maximum_days"]),
            config["timespan"]["$earliest_date__native"],
        ]
    )
    logger.info(f"Checking back until {earliest}")

    all_processed_transactions = []
    for account in accounts:
        logger.info(f"Processing {account}")

        try:
            if test and account.has_account_cache:
                raw_transactions = account.read_account_cache()
                existing_ids = []
            else:
                raw_transactions, existing_ids = process_account(
                    account,
                    accounts_api,
                    budget_id,
                    earliest,
                )
                if test:
                    account.write_account_cache(raw_transactions)

            if account.account_type == AccountType.HOLDING:
                processed_transactions = list(
                    process_holdings(
                        account,
                        raw_transactions,
                        accounts_api,
                        budget_id,
                    )
                )
            else:
                processed_transactions = list(
                    process_account_transactions(
                        account,
                        raw_transactions,
                        cleaner,
                        skippable=existing_ids,
                    )
                )
            logger.info(f"Got {len(processed_transactions)} new transactions")
            all_processed_transactions += processed_transactions
        except Exception:
            logger.exception("Processing %s failed", account)

    if not dry_run and all_processed_transactions:
        result = api.create_transaction(
            budget_id,
            ynab.SaveTransactionsWrapper(transactions=all_processed_transactions),
        )
        if verbose:
            print_results(result)
