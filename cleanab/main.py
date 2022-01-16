from datetime import date, timedelta
from itertools import chain

from logzero import logger

from .apps.base import BaseApp, load_app
from .cleaner import FieldCleaner
from .fints import process_fints_account
from .holdings import process_holdings
from .models.enums import AccountType
from .transactions import process_transaction

TODAY = date.today()


class Cleanab:
    app_connection: BaseApp

    def __init__(self, *, config, dry_run=False, test=False, verbose=False):
        self.config = config
        self.dry_run = dry_run
        self.test = test
        self.verbose = verbose

        if self.test:
            self.dry_run = True
            self.verbose = True

    def setup_app_connection(self):
        App, Config = load_app(self.config.app_module)
        config = Config.parse_obj(self.config.app_config)
        self.app_connection = App(config)

    def setup(self):
        self.setup_app_connection()

        self.accounts = self.config.accounts
        logger.debug("Creating field cleaner instance")
        self.cleaner = FieldCleaner(
            self.config.replacements,
            self.config.finalizer,
        )

        self.earliest = max(
            [
                TODAY - timedelta(days=self.config.timespan.maximum_days),
                self.config.timespan.earliest_date,
            ]
        )
        logger.info(f"Checking back until {self.earliest}")

    def _get_fints_transactions(self, account):
        if self.test and account.has_account_cache:
            raw_transactions = account.read_account_cache()
        else:
            raw_transactions = process_fints_account(
                account,
                earliest=self.earliest,
                latest=TODAY,
            )
            account.write_account_cache(raw_transactions)
        return raw_transactions

    def processor(self, account):
        logger.info(f"Processing {account}")

        try:
            raw_transactions = self._get_fints_transactions(account)

            if account.account_type == AccountType.HOLDING:
                return []
                processed_transactions = list(
                    process_holdings(
                        account,
                        raw_transactions,
                        self.accounts_api,
                        self.budget_id,
                        min_delta=self.config.cleanab.minimum_holdings_delta,
                    )
                )
            else:
                processed_transactions = list(
                    self.process_account_transactions(
                        raw_transactions,
                        account,
                    )
                )
            logger.info(f"Got {len(processed_transactions)} new transactions")
            return processed_transactions
        except Exception:
            logger.exception("Processing %s failed", account)

            return []

    def run(self):
        processed_transactions = list(
            chain.from_iterable(self.processor(account) for account in self.accounts)
        )

        if not processed_transactions:
            logger.warning("No transactions found")
            return

        if self.dry_run:
            logger.info("Dry-run, not creating transactions")
            return

        logger.info(f"Creating transactions in {self.app_connection}")
        new, duplicates = self.app_connection.create_transactions(
            processed_transactions
        )

        logger.info(f"Created {len(new)} new transactions")
        logger.info(f"Saw {len(duplicates)} duplicates")

    def process_account_transactions(self, transactions, account):
        for transaction in transactions:
            yield self.app_connection.augment_transaction(
                process_transaction(transaction, self.cleaner),
                account,
            )
