import logging
import re
from datetime import date
from datetime import timedelta
from hashlib import md5

import yaml
import ynab
from fints.client import FinTS3PinTanClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

today = date.today()


class FieldCleaner:
    def __init__(self, replacements):

        self.cleaners = {}
        for field, contents in replacements.items():
            logger.info(f"Compiling cleaners for {field}")
            self.cleaners[field] = FieldCleaner.compile(contents)

    @staticmethod
    def _replacer_instance(string, replacement=""):
        logger.debug(f"Compiling replacement for '{string}' => '{replacement}'")

        def replace(x):
            if isinstance(x, str):
                return x.replace(string, replacement)
            return x

        return replace

    @staticmethod
    def _regex_sub_instance(pattern, replacement="", casesensitive=False):
        logger.debug(f"Compiling regex for '{pattern}' => '{replacement}'")
        regex = re.compile(pattern, flags=re.IGNORECASE)

        if casesensitive:
            regex = re.compile(pattern)

        def substitute(x):
            if isinstance(x, str):
                return regex.sub(replacement, x)
            return x

        return substitute

    @staticmethod
    def compile(field):
        cleaners = []
        for entry in field:
            if isinstance(entry, str):
                cleaners.append(FieldCleaner._replacer_instance(entry))
            elif isinstance(entry, dict):
                subst = entry.get("repl", "")
                if "string" in entry:
                    cleaners.append(
                        FieldCleaner._replacer_instance(entry["string"], subst)
                    )

                elif "pattern" in entry:
                    casesensitive = entry.get("casesensitive", False)
                    cleaners.append(
                        FieldCleaner._regex_sub_instance(
                            entry["pattern"], subst, casesensitive
                        )
                    )
                else:
                    raise ValueError(f"Missing keyword in definition: {entry}")
            else:
                raise ValueError(f"Replacement definition must be str or dict: {entry}")
        return cleaners

    def clean(self, data):
        for field, cleaners in self.cleaners.items():
            if field in data and data[field] is not None:
                data[field] = data[field].title()
                previous = data[field]
                for cleaner in cleaners:
                    data[field] = cleaner(data[field])

                data[field] = data[field].strip()
                if previous != data[field]:
                    logger.debug(f"Cleaned {field} '{previous}' => '{data[field]}'")

        return data

    @staticmethod
    def lowercase_tld_match(pat):
        return pat.group(1) + pat.group(2).lower()


class Account:
    account_id = None

    def __init__(self, config):
        self.account_id = config["iban"]
        self.ynab_id = config["ynab_id"]
        self.fints = FinTS3PinTanClient(
            config["fints_blz"],
            config["username"],
            config["password"],
            config["fints_endpoint"],
        )

    def retrieve_transactions(self, start_date, end_date=today):
        fints_accounts = self.fints.get_sepa_accounts()
        acc = [acc for acc in fints_accounts if acc.iban == self.account_id][0]
        return self.fints.get_transactions(
            acc, start_date=start_date, end_date=end_date
        )


class Cleanab:
    earliest_date = date(2000, 1, 1)
    max_days_delta = date(2000, 1, 1)
    cleared = False

    def __init__(self, config):

        if "timespan" in config and "maximum_days" in config["timespan"]:
            self.max_days_delta = today - timedelta(
                days=config["timespan"]["maximum_days"]
            )
        if "timespan" in config and "earliest_date" in config["timespan"]:
            self.earliest_date = config["timespan"]["earliest_date"]
        if "mark_cleared" in config["ynab"]:
            self.cleared = config["ynab"]["mark_cleared"]

        self.accounts = [Account(acc_conf) for acc_conf in config["accounts"]]
        self.cleaner = FieldCleaner(config["replacements"])
        self.budget_id = config["ynab"]["budget_id"]

        ynab_conf = ynab.Configuration()
        ynab_conf.api_key["Authorization"] = config["ynab"]["access_token"]
        ynab_conf.api_key_prefix["Authorization"] = "Bearer"
        self.ynab = ynab.TransactionsApi(ynab.ApiClient(ynab_conf))

    def process_accounts(self):
        earliest = max([self.earliest_date, self.max_days_delta])

        for acc in self.accounts:
            transactions = acc.retrieve_transactions(start_date=earliest)
            processed = self.process_transactions(acc.ynab_id, transactions)

            result = self.ynab.bulk_create_transactions(
                self.budget_id, ynab.BulkTransactions(processed)
            )
            logger.debug(result)

    def process_transactions(self, ynab_id, transactions):
        return [
            self._transaction_processor(ynab_id, ta)
            for ta in transactions
            if ta.data["entry_date"] <= today
        ]

    def _transaction_processor(self, ynab_id, transaction):
        entry_date = transaction.data["entry_date"].strftime("%Y-%m-%d")
        data = self.cleaner.clean(transaction.data.copy())
        amount = round(data["amount"].amount * 1000)
        uuid = md5(
            (
                entry_date
                + transaction.data["applicant_name"]
                + (transaction.data.get("purpose", None) or "")
                + str(amount)
            ).encode("utf-8")
        ).hexdigest()

        return {
            "account_id": ynab_id,
            "date": entry_date,
            "amount": amount,
            "payee_name": data["applicant_name"],
            "memo": data["purpose"],
            "import_id": uuid,
            "cleared": "cleared" if self.cleared else "uncleared",
        }


if __name__ == "__main__":
    with open("config.yaml") as fp:
        config = yaml.load(fp, Loader=yaml.FullLoader)

    c = Cleanab(config)
    c.process_accounts()
