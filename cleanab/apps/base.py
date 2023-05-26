from abc import ABC, abstractmethod
from importlib import import_module
from typing import List, Tuple


class BaseApp(ABC):
    @abstractmethod
    def create_transactions(self, transactions) -> Tuple[List, List]:
        return [], []

    @abstractmethod
    def augment_transaction(self, transaction, account):
        pass


def load_app(module_name):
    module = import_module(module_name)
    return module.App, module.Config
