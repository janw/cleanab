import csv
import json
from decimal import Decimal
from functools import partial
from io import StringIO

import requests
from logzero import logger
from pydantic import AnyHttpUrl, BaseModel

from ..models import AccountConfig, FintsTransaction
from .base import BaseApp

_firefly_iii_data_importer_base_config = {
    "version": 3,
    "date": "Y-m-d",
    "delimiter": "comma",
    "headers": True,
    "rules": True,
    "skip_form": True,
    "add_import_tag": True,
    "specifics": [],
    "roles": [
        "account-name",
        "date_transaction",
        "opposing-name",
        "description",
        "amount",
        "external-id",
    ],
    "do_mapping": {
        "0": False,
        "1": False,
        "2": False,
        "3": False,
        "4": False,
        "5": False,
    },
    "mapping": {},
    "duplicate_detection_method": "cell",
    "unique_column_index": 5,
    "unique_column_type": "external-id",
    "ignore_duplicate_lines": False,
    "ignore_duplicate_transactions": True,
    "flow": "csv",
    "date_range": "all",
    "conversion": False,
}


class FireFlyIIIAppConfig(BaseModel):
    fidi_url: AnyHttpUrl
    default_account_id: int
    auto_import_secret: str
    personal_access_token: str


class FireFlyIIIApp(BaseApp):
    _CSV_FIELDNAMES = [
        "account-name",
        "date_transaction",
        "opposing-name",
        "description",
        "amount",
        "external-id",
    ]

    def __init__(self, config: FireFlyIIIAppConfig) -> None:
        self.config = config
        self._set_up_session()
        self._generate_config_json()

    def _set_up_session(self):
        self._post = partial(
            requests.post,
            f"{self.config.fidi_url.rstrip('/')}/autoupload",
            params={"secret": self.config.auto_import_secret},
        )

    def _generate_config_json(self):
        config = _firefly_iii_data_importer_base_config.copy()
        config.update(
            {
                "default_account": self.config.default_account_id,
            }
        )
        self._config_json = json.dumps(config)

    def __str__(self):
        return f"FireFly III FIDI at {self.config.fidi_url}"

    def create_intermediary(self, transactions: list[dict]) -> str:
        importable = StringIO()
        writer = csv.DictWriter(
            importable,
            fieldnames=self._CSV_FIELDNAMES,
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        writer.writerows(transactions)
        return importable.getvalue()

    def create_transactions(self, transactions):
        response = self._post(
            files={
                "importable": self.create_intermediary(transactions).encode("utf-8"),
                "json": self._config_json.encode("utf-8"),
            },
            headers={
                "Authorization": f"Bearer {self.config.personal_access_token}",
                "Accept": "application/json",
            },
        )
        if not response.ok:
            logger.error(f"Failed creating transactions: \n\n{response.text}")
            return [], []

        report = response.text.splitlines()
        logger.info("Received import report:")
        for line in report:
            if trimmed_line := line.strip():
                logger.info(trimmed_line)

        return [], []

    def augment_transaction(
        self, transaction: FintsTransaction, account: AccountConfig
    ):
        payee_name = transaction.applicant_name
        if len(payee_name) > 50:
            payee_name = payee_name[:50]

        return {
            "account-name": account.friendly_name,
            "date_transaction": transaction.date.isoformat(),
            "opposing-name": transaction.applicant_name or "Unnamed",
            "description": transaction.purpose,
            "amount": str(Decimal(transaction.amount) / 1000),
            "external-id": transaction.import_id,
        }


Config = FireFlyIIIAppConfig
App = FireFlyIIIApp
