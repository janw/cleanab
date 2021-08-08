from datetime import date
from hashlib import md5


def process_holdings(account, holdings, api, budget_id):
    ynab_acc = api.get_account_by_id(account_id=account.ynab_id, budget_id=budget_id)

    entry_date = date.today()
    entry_date = entry_date.strftime("%Y-%m-%d")
    balance_holdings = round(sum([h["total_value"] for h in holdings]) * 1000)
    balance_ynab = ynab_acc.data.account.balance
    amount = balance_holdings - balance_ynab

    if amount == 0:
        return None

    uuid = md5(
        (entry_date + "Value Adjustment" + "" + str(amount)).encode("utf-8")
    ).hexdigest()

    yield {
        "account_id": account.ynab_id,
        "date": entry_date,
        "amount": amount,
        "payee_name": "Value Adjustment",
        "import_id": uuid,
        "cleared": "cleared" if account.default_cleared else "uncleared",
        "approved": account.default_approved,
    }
