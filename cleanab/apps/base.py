from abc import ABC, abstractmethod
from importlib import import_module
from typing import List, Tuple


class BaseApp(ABC):
    def get_accounts(self):
        pass

    def get_account_balance(self):
        pass

    def create_intermediary(self):
        pass

    @abstractmethod
    def create_transactions(self, transactions) -> Tuple[List, List]:
        return [], []

    def augment_transaction(self, transaction, account):
        pass


def load_app(module_name):
    module = import_module(module_name)
    return module.App, module.Config
