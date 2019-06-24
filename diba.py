import logging
import re
from datetime import date
from datetime import timedelta
from hashlib import md5
from pprint import pprint

import yaml
import ynab
from fints.client import FinTS3PinTanClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


def retrieve_transactions(account_id, fints, start_date, end_date):
    acc = [acc for acc in fints.get_sepa_accounts() if acc.iban == account_id][0]
    return fints.get_transactions(acc, start_date=start_date, end_date=end_date)


def process_transactions(account_id, transactions, cleaner):
    for ta in transactions:
        entry_date = ta.data["entry_date"]
        if entry_date > date.today():
            continue
        entry_date = entry_date.strftime("%Y-%m-%d")
        data = cleaner.clean(ta.data.copy())
        amount = round(data["amount"].amount * 1000)
        uuid = md5(
            (
                entry_date
                + ta.data["applicant_name"]
                + (ta.data.get("purpose", None) or "")
                + str(amount)
            ).encode("utf-8")
        ).hexdigest()

        yield {
            "account_id": account_id,
            "date": entry_date,
            "amount": amount,
            "payee_name": data["applicant_name"],
            "memo": data["purpose"],
            "import_id": uuid,
        }


def main():
    with open("config.yaml") as fp:
        config = yaml.load(fp, Loader=yaml.FullLoader)

    cleaner = FieldCleaner(config["replacements"])

    ynab_conf = ynab.Configuration()
    ynab_conf.api_key["Authorization"] = config["ynab"]["access_token"]
    ynab_conf.api_key_prefix["Authorization"] = "Bearer"
    api = ynab.TransactionsApi(ynab.ApiClient(ynab_conf))

    for account in config["accounts"]:
        account_id = account["iban"]
        fints = FinTS3PinTanClient(
            account["fints_blz"],
            account["username"],
            account["password"],
            account["fints_endpoint"],
        )

        today = date.today()
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
            process_transactions(account["ynab_id"], transactions, cleaner)
        )
        result = api.bulk_create_transactions(
            config["ynab"]["budget_id"], ynab.BulkTransactions(processed)
        )
        pprint(result)


if __name__ == "__main__":
    main()
