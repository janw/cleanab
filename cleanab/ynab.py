from functools import lru_cache

import ynab_api as ynab


@lru_cache(maxsize=1)
def get_ynab_api(access_token):
    ynab_conf = ynab.Configuration()
    ynab_conf.api_key["Authorization"] = access_token
    ynab_conf.api_key_prefix["Authorization"] = "Bearer"
    return ynab.TransactionsApi(ynab.ApiClient(ynab_conf))


@lru_cache(maxsize=1)
def get_ynab_account_api(access_token):
    ynab_conf = ynab.Configuration()
    ynab_conf.api_key["Authorization"] = access_token
    ynab_conf.api_key_prefix["Authorization"] = "Bearer"
    return ynab.AccountsApi(ynab.ApiClient(ynab_conf))


def create_transactions(access_token, budget_id, processed_transactions):
    return get_ynab_api(access_token).create_transaction(
        budget_id,
        ynab.SaveTransactionsWrapper(transactions=processed_transactions),
    )
