from uuid import UUID

from pydantic import BaseModel
from ynab_api.api_client import ApiClient
from ynab_api.apis import AccountsApi, TransactionsApi
from ynab_api.configuration import Configuration
from ynab_api.model.save_transaction import SaveTransaction
from ynab_api.model.save_transactions_wrapper import SaveTransactionsWrapper

from ..models import AccountConfig, FintsTransaction
from .base import BaseApp

API_URL = "https://api.youneedabudget.com/v1"


class NewYnabConfig(BaseModel):
    access_token: str
    budget_id: UUID


class NewYnabApp(BaseApp):
    def __init__(self, config) -> None:
        self._access_token = config.access_token
        self._budget_id = str(config.budget_id)
        self._api_client = self._create_ynab_api_client(self._access_token)

    def __str__(self):
        return f"YNAB Budget {self._budget_id}"

    def _create_ynab_api_client(self, access_token):
        ynab_conf = Configuration(
            host=API_URL,
        )
        ynab_conf.api_key["bearer"] = access_token
        ynab_conf.api_key_prefix["bearer"] = "Bearer"
        return ApiClient(ynab_conf)

    def create_transactions(self, transactions):
        api = TransactionsApi(self._api_client)
        result = api.create_transaction(
            self._budget_id,
            SaveTransactionsWrapper(transactions=transactions),
        )
        duplicates = getattr(result.data, "duplicate_import_ids", [])
        new = getattr(result.data, "transaction_ids", [])

        return new, duplicates

    def get_account_balance(self, account_id):
        api = AccountsApi(self._api_client)
        account = api.get_account_by_id(
            account_id=account_id,
            budget_id=self._budget_id,
        )
        return account.data.account.balance

    def augment_transaction(
        self, transaction: FintsTransaction, account: AccountConfig
    ):
        payee_name = transaction.applicant_name
        if len(payee_name) > 50:
            payee_name = payee_name[:50]

        return SaveTransaction(
            date=transaction.date,
            amount=transaction.amount,
            payee_name=payee_name,
            memo=transaction.purpose,
            import_id=transaction.import_id,
            account_id=account.per_app_id,
            cleared="cleared" if account.default_cleared else "uncleared",
            approved=account.default_approved,
        )


Config = NewYnabConfig
App = NewYnabApp
