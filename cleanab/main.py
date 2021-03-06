from datetime import date
from datetime import timedelta

import yaml
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


def main(dry_run, configfile):
    logger.debug("Loading config file")
    config = yaml.safe_load(configfile)
    api = get_ynab_api(config)
    accounts_api = get_ynab_account_api(config)
    budget_id = config["ynab"]["budget_id"]

    accounts = [Account(**acc) for acc in config["accounts"]]

    logger.debug("Creating field cleaner instance")
    cleaner = FieldCleaner(
        config.get("pre-replacements", []), config.get("replacements", [])
    )

    today = date.today()
    earliest = max(
        [
            today - timedelta(days=config["timespan"]["maximum_days"]),
            config["timespan"]["earliest_date"],
        ]
    )
    logger.info(f"Checking back until {earliest}")

    processed = []
    for account in accounts:
        logger.info(f"Processing account {account.iban}")

        fints = FinTS3PinTanClient(
            account.fints_blz,
            account.fints_username,
            account.fints_password,
            account.fints_endpoint,
        )
        if account.account_type == AccountType.HOLDING:
            holdings = retrieve_holdings(account, fints)

            new_transactions = process_holdings(
                account,
                holdings,
                accounts_api,
                budget_id,
            )
        else:
            transactions = retrieve_transactions(
                account, fints, start_date=earliest, end_date=today
            )
            try:
                existing_transactions = api.get_transactions(
                    budget_id, since_date=earliest
                )
                existing_ids = [
                    t.import_id
                    for t in existing_transactions.data.transactions
                    if t.import_id
                ]
            except Exception:
                logger.error("Could not retrieve existing transactions")
                existing_ids = []

            new_transactions = list(
                process_transactions(
                    account,
                    transactions,
                    cleaner,
                    skippable=existing_ids,
                )
            )
            logger.debug(f"Got {len(new_transactions)} new transactions")

        processed += new_transactions

    if not dry_run and processed:
        result = api.create_transaction(
            budget_id, ynab.SaveTransactionsWrapper(transactions=processed)
        )
        print_results(result)

    # dupes = getattr(result.data, "duplicate_import_ids", [])
    # if dupes:
    #     logger.info("Updating duplicates")
    #     updateable = list(filter(lambda x: x["import_id"] in dupes, processed))
    #     transactions = ynab.SaveTransactionsWrapper(transactions=updateable)
    #     api.update_transactions(budget_id, transactions)
