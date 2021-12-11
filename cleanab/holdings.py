from datetime import date
from hashlib import md5


def process_holdings(account, holdings, api, budget_id, min_delta=0):
    ynab_acc = api.get_account_by_id(account_id=account.per_app_id, budget_id=budget_id)

    entry_date = date.today()
    entry_date = entry_date.strftime("%Y-%m-%d")
    balance_holdings = round(sum([h["total_value"] for h in holdings]) * 1000)
    balance_ynab = ynab_acc.data.account.balance
    amount = balance_holdings - balance_ynab

    if amount == 0 or amount < min_delta * 1000:
        return None

    balance_in = balance_holdings / 1000
    balance_out = balance_ynab / 1000
    amount_adj = amount / 1000

    uuid = md5(
        (entry_date + "Value Adjustment" + "" + str(amount)).encode("utf-8")
    ).hexdigest()

    yield {
        "account_id": account.per_app_id,
        "date": entry_date,
        "amount": amount,
        "payee_name": "Value Adjustment",
        "memo": (
            "Adjusting account balance: "
            f"{balance_in:.2f} - {amount_adj:.2f} = {balance_out:.2f}"
        ),
        "import_id": uuid,
        "cleared": "cleared" if account.default_cleared else "uncleared",
        "approved": account.default_approved,
    }
