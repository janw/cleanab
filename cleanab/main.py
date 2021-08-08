from concurrent.futures import ThreadPoolExecutor
from datetime import date
from datetime import timedelta
from itertools import chain

from logzero import logger

from cleanab import ynab
from cleanab.cleaner import FieldCleaner
from cleanab.fints import process_account
from cleanab.formatter import print_results
from cleanab.holdings import process_holdings
from cleanab.transactions import process_account_transactions
from cleanab.types import Account
from cleanab.types import AccountType

TODAY = date.today()


class Cleanab:
    def __init__(self, *, config, dry_run=False, test=False, verbose=False):
        self.config = config
        self.dry_run = dry_run
        self.test = test
        self.verbose = verbose

        if self.test:
            self.dry_run = True
            self.verbose = True

    def setup(self):
        self._ynab_access_token = self.config["ynab"]["access_token"]
        self.accounts_api = ynab.get_ynab_account_api(self._ynab_access_token)
        self.budget_id = self.config["ynab"]["budget_id"]

        self.accounts = [Account(**acc) for acc in self.config["accounts"]]
        logger.debug("Creating field cleaner instance")
        self.cleaner = FieldCleaner(
            self.config.get("replacements", []),
            self.config["finalizer"],
            self.verbose,
        )

        self.earliest = max(
            [
                TODAY - timedelta(days=self.config["timespan"]["maximum_days"]),
                self.config["timespan"]["$earliest_date__native"],
            ]
        )
        logger.info(f"Checking back until {self.earliest}")

    def processor(self, account):
        logger.info(f"Processing {account}")

        try:
            if self.test and account.has_account_cache:
                raw_transactions = account.read_account_cache()
                existing_ids = []
            else:
                raw_transactions, existing_ids = process_account(
                    account,
                    earliest=self.earliest,
                    latest=TODAY,
                )
                if self.test:
                    account.write_account_cache(raw_transactions)

            if account.account_type == AccountType.HOLDING:
                processed_transactions = list(
                    process_holdings(
                        account,
                        raw_transactions,
                        self.accounts_api,
                        self.budget_id,
                    )
                )
            else:
                processed_transactions = list(
                    process_account_transactions(
                        account,
                        raw_transactions,
                        self.cleaner,
                        skippable=existing_ids,
                    )
                )
            logger.info(f"Got {len(processed_transactions)} new transactions")
            return processed_transactions
        except Exception:
            logger.exception("Processing %s failed", account)

            return []

    def run(self):
        num_workers = self.config["cleanab"]["concurrency"]
        logger.info(f"Parallelizing with {num_workers} workers")

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            tasks = [
                executor.submit(self.processor, account) for account in self.accounts
            ]
        processed_transactions = list(chain.from_iterable((t.result() for t in tasks)))

        if not processed_transactions:
            logger.warning("No transactions found")
            return

        if self.dry_run:
            logger.info("Dry-run, not creating YNAB transactions")
            return

        logger.info("Creating YNAB transactions")
        result = ynab.create_transactions(
            self._ynab_access_token, self.budget_id, processed_transactions
        )

        print_results(result, verbose=self.verbose)
