import re
from datetime import date
from hashlib import md5

from logzero import logger


re_cc_purpose = re.compile(r"^(.+?)([A-Z]{3})\s{3,}([0-9,]+)(.*)$")


def process_account_transactions(account, transactions, cleaner, skippable=None):
    for transaction in transactions:
        yield from process_transaction(account, transaction, cleaner)


def process_transaction(account, transaction, cleaner):
    data = transaction

    entry_date = data.get("entry_date") or data["date"]
    if entry_date > date.today():
        return

    entry_date = entry_date.strftime("%Y-%m-%d")
    amount = round(data["amount"].amount * 1000)
    applicant_name = data.get("applicant_name", None) or ""
    purpose = data.get("purpose", None) or ""
    uuid = md5(
        (entry_date + applicant_name + purpose + str(amount)).encode("utf-8")
    ).hexdigest()

    local_data = data.copy()
    if len(applicant_name) == 0 and len(purpose) > 0:
        result = re_cc_purpose.search(purpose)
        if result:
            splits = result.groups()
            local_data["applicant_name"] = splits[0]
            local_data["purpose"] = " ".join(splits[1:])

    local_data = cleaner.clean(local_data)

    echo_if_changed(data, local_data, cleaner=cleaner, uuid=uuid)

    purpose = local_data.get("purpose", "")
    if purpose and len(purpose) > 200:
        purpose = purpose[:200]

    yield {
        "account_id": account.ynab_id,
        "date": entry_date,
        "amount": amount,
        "payee_name": local_data["applicant_name"],
        "memo": purpose,
        "import_id": uuid,
        "cleared": "cleared" if account.default_cleared else "uncleared",
        "approved": account.default_approved,
    }


def echo_if_changed(original_data, data, *, cleaner, uuid):
    logger.debug("---")
    logger.debug("Transaction %s", uuid)

    for field in cleaner.fields:
        previous = original_data.get(field, "") or ""
        cleaned = data.get(field, "") or ""

        log = logger.info
        prefix_in = prefix_out = "  "
        if previous != cleaned:
            log = logger.warning
            prefix_in = "--"
            prefix_out = "++"

        log("%16s %s %s", field, prefix_in, previous)
        log("%16s %s %s", field, prefix_out, cleaned)
