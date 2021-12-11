from datetime import date

from pydantic import BaseModel


class FintsTransaction(BaseModel):
    date: date
    amount: int
    applicant_name: str
    purpose: str
    import_id: str = ""
