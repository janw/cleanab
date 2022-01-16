from datetime import date

from pydantic import BaseModel, validator


class FintsTransaction(BaseModel):
    date: date
    amount: int
    applicant_name: str
    purpose: str = ""
    import_id: str = ""

    @validator("purpose", pre=True)
    def set_purpose_empty(cls, purpose):
        return purpose or ""
