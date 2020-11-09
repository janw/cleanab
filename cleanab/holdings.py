from datetime import date
from hashlib import md5


def retrieve_holdings(account_id, fints):
    acc = [acc for acc in fints.get_sepa_accounts() if acc.iban == account_id][0]
    return fints.get_holdings(acc)


def process_holdings(holdings, api, budget_id, ynab_id):
    ynab_acc = api.get_account_by_id(account_id=ynab_id, budget_id=budget_id)

    entry_date = date.today()
    entry_date = entry_date.strftime("%Y-%m-%d")
    balance_holdings = round(sum([h.total_value for h in holdings]) * 1000)
    balance_ynab = ynab_acc.data.account.balance
    amount = balance_holdings - balance_ynab

    if amount == 0:
        return None

    uuid = md5(
        (entry_date + "Valuation Adjustment" + "" + str(amount)).encode("utf-8")
    ).hexdigest()

    yield {
        "account_id": ynab_id,
        "date": entry_date,
        "amount": amount,
        "payee_name": "Valuation Adjustment",
        "import_id": uuid,
        # "cleared": "cleared" if cleared else "uncleared",
    }
