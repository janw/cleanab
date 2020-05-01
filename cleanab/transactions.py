from datetime import date
from hashlib import md5


def retrieve_transactions(account_id, fints, start_date, end_date):
    acc = [acc for acc in fints.get_sepa_accounts() if acc.iban == account_id][0]
    return fints.get_transactions(acc, start_date=start_date, end_date=end_date)


def process_transactions(account_id, transactions, cleaner, cleared=False):
    for ta in transactions:
        if "entry_date" in ta.data:
            entry_date = ta.data["entry_date"]
        else:
            entry_date = ta.data["date"]

        if "entry_date" in ta.data:
            entry_date = ta.data["entry_date"]
        else:
            entry_date = ta.data["date"]

        if entry_date > date.today():
            continue
        entry_date = entry_date.strftime("%Y-%m-%d")
        data = cleaner.clean(ta.data.copy())
        amount = round(data["amount"].amount * 1000)
        uuid = md5(
            (
                entry_date
                + (ta.data.get("applicant_name", None) or "")
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
            "cleared": "cleared" if cleared else "uncleared",
        }