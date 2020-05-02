from datetime import date
from datetime import timedelta

import yaml
import ynab
from fints.client import FinTS3PinTanClient
from logzero import logger

from cleanab.cleaner import FieldCleaner
from cleanab.formatter import print_results
from cleanab.transactions import process_transactions
from cleanab.transactions import retrieve_transactions


def main(dry_run, configfile):
    logger.debug("Loading config file")
    config = yaml.safe_load(configfile)

    logger.debug("Creating field cleaner instance")
    cleaner = FieldCleaner(
        config.get("pre-replacements", []), config.get("replacements", [])
    )

    ynab_conf = ynab.Configuration()
    ynab_conf.api_key["Authorization"] = config["ynab"]["access_token"]
    ynab_conf.api_key_prefix["Authorization"] = "Bearer"
    api = ynab.TransactionsApi(ynab.ApiClient(ynab_conf))
    today = date.today()

    for account in config["accounts"]:
        account_id = account["iban"]
        fints = FinTS3PinTanClient(
            account["fints_blz"],
            account["username"],
            account["password"],
            account["fints_endpoint"],
        )

        earliest = max(
            [
                today - timedelta(days=config["timespan"]["maximum_days"]),
                config["timespan"]["earliest_date"],
            ]
        )
        transactions = retrieve_transactions(
            account_id, fints, start_date=earliest, end_date=today
        )

        processed = list(
            process_transactions(
                account["ynab_id"],
                transactions,
                cleaner,
                cleared=config["ynab"].get("mark_cleared", False),
            )
        )
    if not dry_run:
        result = api.bulk_create_transactions(
            config["ynab"]["budget_id"], ynab.BulkTransactions(processed)
        )

        print_results(result)
