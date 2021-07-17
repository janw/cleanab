import re
from datetime import date
from hashlib import md5


def retrieve_transactions(account, fints, start_date, end_date):
    acc = [acc for acc in fints.get_sepa_accounts() if acc.iban == account.iban][0]
    return fints.get_transactions(acc, start_date=start_date, end_date=end_date)


re_cc_purpose = re.compile(r"^(.+?)([A-Z]{3})\s{3,}([0-9,]+)(.*)$")


def process_transactions(account, transactions, cleaner, skippable=None):
    skippable = [] if not skippable else skippable

    for ta in transactions:
        if "entry_date" in ta.data:
            entry_date = ta.data["entry_date"]
        else:
            entry_date = ta.data["date"]

        if entry_date > date.today():
            continue

        entry_date = entry_date.strftime("%Y-%m-%d")
        amount = round(ta.data["amount"].amount * 1000)
        applicant_name = ta.data.get("applicant_name", None) or ""
        purpose = ta.data.get("purpose", None) or ""
        uuid = md5(
            (entry_date + applicant_name + purpose + str(amount)).encode("utf-8")
        ).hexdigest()

        # if uuid in skippable:
        #     continue

        local_data = ta.data.copy()
        if len(applicant_name) == 0 and len(purpose) > 0:
            result = re_cc_purpose.search(purpose)
            if result:
                splits = result.groups()
                local_data["applicant_name"] = splits[0]
                local_data["purpose"] = " ".join(splits[1:])

        local_data = cleaner.clean(local_data)
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
